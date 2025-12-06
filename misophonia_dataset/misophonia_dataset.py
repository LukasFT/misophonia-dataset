import concurrent.futures
import itertools
import json
import os
import uuid
import warnings
from pathlib import Path

import numpy as np
import soundfile as sf
from tqdm import tqdm

from .interface import (
    GlobalMixingParams,
    MisophoniaDataset,
    MisophoniaDatasetSplit,
    MisophoniaItem,
    SourceData,
    SourceDataItem,
    SplitT,
)


class GeneratedMisophoniaDataset(MisophoniaDataset):
    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        self._items_by_split: dict[SplitT, list[SourceDataItem]] | None = None

    def prepare(self) -> None:
        if self._items_by_split is not None:
            return

        assert all(ds.is_downloaded() for ds in self._source_data), "All source data must be downloaded."

        all_source_data = tuple(itertools.chain.from_iterable(ds.get_metadata() for ds in self._source_data))

        items_by_split: dict[SplitT, list[SourceDataItem]] = {"train": [], "val": [], "test": []}
        for item in all_source_data:
            items_by_split[item.split].append(item)

        self._items_by_split = items_by_split

    def get_split(
        self,
        split: SplitT,
        *,
        num_samples: int,
        foregrounds_per_item: tuple[int, int] = (1, 1),
        backgrounds_per_item: tuple[int, int] = (1, 3),
        trig_to_control_ratio: float = 0.5,
        random_seed: int = 42,
        n_paired_sounds: int = 0,  # TODO
        min_length: int | None = None,  # TODO
    ) -> MisophoniaDatasetSplit:
        from .mixing import binaural_mix, prepare_track_specs

        if split == "test":
            warnings.warn(
                """You are generating a new test dataset that is not the canonical version. """
                """Please do not use this for comparisons across different papers. """
                """See PremadeMisophoniaDataset for loading the canonical test dataset.""",
                UserWarning,
            )

        self.prepare()
        all_items: list[SourceDataItem] = self._items_by_split[split]

        all_trig_items = [it for it in all_items if it.label_type == "trigger"]
        all_ctrl_items = [it for it in all_items if it.label_type == "control"]
        all_bg_items = [it for it in all_items if it.label_type == "background"]

        def _prepare_samples():  # noqa: ANN202
            """Prepare sample indices and random seeds for dataset generation."""
            rng_plan = np.random.default_rng(seed=random_seed)

            def make_cycle(n: int):  # noqa: ANN202
                """Yield indices 0..n-1 in random order, then reshuffle and repeat."""
                order = np.arange(n)
                while True:
                    rng_plan.shuffle(order)
                    for idx in order:
                        yield int(idx)

            trig_cycle = make_cycle(len(all_trig_items)) if all_trig_items else None
            ctrl_cycle = make_cycle(len(all_ctrl_items)) if all_ctrl_items else None
            bg_cycle = make_cycle(len(all_bg_items))

            is_trig_for_item: list[bool] = []
            fg_indices_for_item: list[list[int]] = []
            bg_indices_for_item: list[list[int]] = []
            seeds_for_item = rng_plan.integers(0, 2**32 - 1, size=num_samples, dtype=np.uint32)

            for _ in range(num_samples):
                num_fg = int(rng_plan.integers(foregrounds_per_item[0], foregrounds_per_item[1] + 1))
                num_bg = int(rng_plan.integers(backgrounds_per_item[0], backgrounds_per_item[1] + 1))

                # Decide trigger vs control
                is_trig = bool(rng_plan.random() < trig_to_control_ratio)
                if is_trig and not all_trig_items:
                    # fall back to control if no trig items
                    is_trig = False
                if (not is_trig) and not all_ctrl_items:
                    # fall back to trigger if no control items
                    is_trig = True

                is_trig_for_item.append(is_trig)

                # Foreground indices from the appropriate cycle
                if is_trig:
                    if trig_cycle is None:
                        raise RuntimeError("No trigger items but attempted to sample trigger foregrounds.")
                    fg_cycle = trig_cycle
                else:
                    if ctrl_cycle is None:
                        raise RuntimeError("No control items but attempted to sample control foregrounds.")
                    fg_cycle = ctrl_cycle

                fg_indices = [next(fg_cycle) for _ in range(num_fg)]
                bg_indices = [next(bg_cycle) for _ in range(num_bg)]

                fg_indices_for_item.append(fg_indices)
                bg_indices_for_item.append(bg_indices)
            return is_trig_for_item, fg_indices_for_item, bg_indices_for_item, seeds_for_item

        is_trig_for_item, fg_indices_for_item, bg_indices_for_item, seeds_for_item = _prepare_samples()

        def _generate_one(index: int) -> MisophoniaItem:
            rng = np.random.default_rng(int(seeds_for_item[index]))
            is_trig = is_trig_for_item[index]
            fg_idxs = fg_indices_for_item[index]
            bg_idxs = bg_indices_for_item[index]

            fg_pool = all_trig_items if is_trig else all_ctrl_items
            foreground_items = [fg_pool[j] for j in fg_idxs]
            background_items = [all_bg_items[j] for j in bg_idxs]

            foreground_categories = tuple(set(itertools.chain.from_iterable(it.labels for it in foreground_items)))
            background_categories = tuple(set(itertools.chain.from_iterable(it.labels for it in background_items)))

            global_params = GlobalMixingParams(_rng=rng)

            foreground_specs, background_specs = prepare_track_specs(
                foreground_items,
                background_items,
                global_params=global_params,
                bg_track_options={"level": 0.7},  # TODO: Why this?
                rng=rng,
            )
            foreground_tracks, _ = tuple(zip(*foreground_specs))
            background_tracks, _ = tuple(zip(*background_specs))

            mix, ground_truth = binaural_mix(
                fg_tracks=foreground_specs,
                bg_tracks=background_specs,
                global_params=global_params,
                is_trig=is_trig,
            )

            return MisophoniaItem(
                split=split,
                is_trigger=is_trig,
                foreground_categories=foreground_categories,
                background_categories=background_categories,
                mix=mix,
                ground_truth=ground_truth,
                length=mix.shape[1],
                global_mixing_params=global_params,
                foregrounds=foreground_tracks,
                backgrounds=background_tracks,
            )

        return MisophoniaDatasetSplit(
            split=split,
            num_samples=num_samples,
            get_one=_generate_one,
        )


class PremadeMisophoniaDataset(MisophoniaDataset):
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self._items_by_split: dict[SplitT, list[MisophoniaItem]] | None = None

    def prepare(self) -> None:
        if self._items_by_split is not None:
            return

        self._items_by_split = {"train": [], "val": [], "test": []}

        for split in self._items_by_split.keys():
            split_dir = self.base_dir / split
            metadata_file = split_dir / "metadata.jsonl"
            if not metadata_file.exists():
                continue

            with metadata_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    obj = json.loads(line)
                    obj["mix"] = split_dir / obj["mix"]
                    obj["ground_truth"] = split_dir / obj["ground_truth"] if obj["ground_truth"] is not None else None
                    item = MisophoniaItem.model_validate(obj)
                    self._items_by_split[split].append(item)

    def get_split(
        self,
        split: SplitT,
    ) -> MisophoniaDatasetSplit:
        self.prepare()
        items = self._items_by_split[split]

        if items is None or len(items) == 0:
            raise ValueError(f"No data available for split '{split}'")

        return MisophoniaDatasetSplit(
            split=split,
            num_samples=len(items),
            get_one=items.__getitem__,  # Get the pre-computed item directly from the list
        )


def save_miso_dataset(
    split_data: MisophoniaDatasetSplit,
    *,
    base_dir: Path | None = None,
    n_workers: int | None = None,
    show_progress: bool = False,
) -> None:
    base_dir = base_dir if base_dir is not None else Path(__file__).parent.parent / "data" / "mixed"

    split = split_data.split

    split_dir = base_dir / split
    mix_dir = split_dir / "mixes"
    gt_dir = split_dir / "ground_truths"
    metadata_file = split_dir / "metadata.jsonl"

    if split_dir.exists():
        raise FileExistsError(f"Directory for split '{split}' already exists at {split_dir}")

    mix_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)

    def _generate_and_save(i: int) -> str:
        item: MisophoniaItem = split_data[i]  # Heavy work (mixing + I/O) happens here

        mix_id = str(uuid.uuid4())

        mix_file = mix_dir / f"{mix_id}.wav"
        sf.write(
            mix_file,
            np.transpose(item.mix),
            samplerate=item.global_mixing_params.sample_rate,
            subtype="PCM_24",
        )

        gt_file = None
        if item.ground_truth is not None:
            gt_file = gt_dir / f"{mix_id}.wav"
            sf.write(
                gt_file,
                np.transpose(item.ground_truth),
                samplerate=item.global_mixing_params.sample_rate,
                subtype="PCM_24",
            )

        item_with_paths = item.model_copy(
            update={
                "uuid": mix_id,
                "mix": mix_file.relative_to(split_dir),
                "ground_truth": gt_file.relative_to(split_dir) if gt_file is not None else None,
            }
        )
        return item_with_paths.model_dump_json(round_trip=True)

    n_workers = n_workers if n_workers is not None else (os.cpu_count() or 1)
    size = len(split_data)

    with metadata_file.open("w", buffering=1, encoding="utf-8") as metadata_f:
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            results = executor.map(_generate_and_save, range(size))
            if show_progress:
                results = tqdm(results, total=size, desc=f"Saving {split} items")
            for row in results:
                metadata_f.write(row + "\n")
