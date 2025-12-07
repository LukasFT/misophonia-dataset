import concurrent.futures
import itertools
import json
import os
import shutil
import uuid
import warnings
from pathlib import Path
from typing import Literal

import eliot
import numpy as np
import soundfile as sf
from tqdm import tqdm

from ._analysis import models_to_df
from .interface import (
    GlobalMixingParams,
    MisophoniaDataset,
    MisophoniaDatasetSplit,
    MisophoniaItem,
    SourceData,
    SourceDataItem,
    SplitT,
    get_default_data_dir,
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
                fg_specs=foreground_specs,
                bg_specs=background_specs,
                global_params=global_params,
                is_trig=is_trig,
            )

            return MisophoniaItem(
                split=split,
                is_trigger=is_trig,
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
    def __init__(self, name: str, base_save_dir: Path | str | None = None) -> None:
        self.name = name
        self._base_save_dir = base_save_dir
        self._all_splits_dir = get_default_data_dir(dataset_name=self.name, base_dir=self._base_save_dir)
        self._items_by_split: dict[SplitT, list[MisophoniaItem]] | None = None

    def prepare(self) -> None:
        if self._items_by_split is not None:
            return

        self._items_by_split = {"train": [], "val": [], "test": []}

        for split in self._items_by_split.keys():
            split_dir = self._all_splits_dir / split
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

    def save_split(
        self,
        split_data: MisophoniaDatasetSplit,
        *,
        n_workers: int | None = None,
        show_progress: bool = False,
        if_exists: Literal["error", "replace", "append"] = "error",
    ) -> None:
        split = split_data.split

        split_dir = self._all_splits_dir / split
        mix_dir = split_dir / "mixes"
        gt_dir = split_dir / "ground_truths"
        metadata_file = split_dir / "metadata.jsonl"

        if split_dir.exists():
            if if_exists == "error":
                raise FileExistsError(f"Directory for split '{split}' already exists at {split_dir}")
            if if_exists == "replace":
                eliot.log_message(f"Replacing existing directory at {split_dir}", level="info")
                shutil.rmtree(split_dir)
            if if_exists == "append":
                eliot.log_message(f"Appending to existing directory at {split_dir}", level="info")

        mix_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)

        def _generate_and_save(i: int) -> str:
            item: MisophoniaItem = split_data[i]  # Heavy work (mixing + I/O) happens here

            mix_id = str(uuid.uuid4())

            mix_file = mix_dir / f"{mix_id}.wav"
            sf.write(
                mix_file,
                np.transpose(item.get_mix_audio()),
                samplerate=item.global_mixing_params.sample_rate,
                subtype="PCM_24",
            )

            gt_file = None
            if item.ground_truth is not None:
                gt_file = gt_dir / f"{mix_id}.wav"
                sf.write(
                    gt_file,
                    np.transpose(item.get_ground_truth_audio()),
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

        with metadata_file.open("a", buffering=1, encoding="utf-8") as metadata_f:
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
                results = executor.map(_generate_and_save, range(size))
                if show_progress:
                    results = tqdm(results, total=size, desc=f"Saving {split} items")
                for row in results:
                    metadata_f.write(row + "\n")

    def __repr__(self) -> str:
        return f"<PremadeMisophoniaDataset from {self._all_splits_dir}>"


def add_experimental_pairs_to_dataset(
    original: PremadeMisophoniaDataset,
    *,
    split: SplitT,
    seed: int = 42,
) -> None:
    from .mixing import binaural_mix

    eliot.log_message(f"Adding experimental pairs to dataset split '{split}' with seed {seed}", level="info")
    eliot.log_message(f"Loading base dataset from {original._all_splits_dir}", level="debug")
    original.prepare()

    original_split = original.get_split(split)

    # Only include single-foreground items
    all_items = models_to_df(original_split, flatten=True)
    all_items = all_items[all_items["len(foregrounds)"] == 1]
    all_items = all_items[all_items["len(foreground_categories)"] == 1]

    control_items = all_items[~all_items["is_trigger"]]

    trigger_items = all_items[all_items["is_trigger"]]
    trigger_items = trigger_items[trigger_items["len(foregrounds)"] == 1]
    trigger_items = trigger_items[trigger_items["len(foreground_categories)"] == 1]

    assert trigger_items["len(foregrounds[0][source_item][validated_by])"].dropna().eq(1).all(), (
        "Some entries have multiple validators, which is not yet supported"
    )

    trigger_items["is_foams"] = trigger_items["foregrounds[0][source_item][validated_by][0]"] == "FOAMS"

    foams_sounds = trigger_items[trigger_items["is_foams"]]
    non_foams_sounds = trigger_items[~trigger_items["is_foams"]]

    # Sort to make reproducable
    trigger_categories = tuple(sorted(trigger_items["foreground_categories[0]"].unique()))

    # Sample
    rng = np.random.default_rng(seed)

    trig_samples: list[MisophoniaItem] = []

    for category in trigger_categories:
        # sample one what is foams and one not
        foams_in_category = foams_sounds[foams_sounds["foreground_categories[0]"] == category]
        non_foams_in_category = non_foams_sounds[non_foams_sounds["foreground_categories[0]"] == category]

        # Sample one from each
        if len(foams_in_category) == 0:
            eliot.log_message(f"No FOAMS samples found in category '{category}'", level="warning")
        else:
            sample_i = rng.integers(len(foams_in_category))
            trig_samples.append(foams_in_category.iloc[sample_i]["_model"])

        if len(non_foams_in_category) == 0:
            eliot.log_message(f"No non-FOAMS samples found in category '{category}'", level="warning")
        else:
            sample_i = rng.integers(len(non_foams_in_category))
            trig_samples.append(non_foams_in_category.iloc[sample_i]["_model"])

    if len(control_items) < len(trig_samples):
        raise ValueError("Not enough control items to match the number of trigger samples")

    control_samples = rng.choice(control_items.index, size=len(trig_samples), replace=False)
    control_samples = control_items.loc[control_samples]["_model"]
    samples: list[tuple[MisophoniaItem, MisophoniaItem]] = list(zip(trig_samples, control_samples))

    def _get_one(index: int) -> MisophoniaItem:
        original_trig, original_control = samples[index]

        assert original_control.uuid is not None, "Original control item must have a UUID"

        global_mixing_params = original_trig.global_mixing_params
        sample_rate = global_mixing_params.sample_rate
        bg_specs = tuple(
            # Keep the backgrounds the same
            (track, track.source_item.load_audio(sample_rate=sample_rate)[0])
            for track in original_trig.backgrounds
        )
        bg_tracks, _ = zip(*bg_specs)

        original_control_track = original_control.foregrounds[0]
        control_item = original_control_track.source_item
        control_audio = control_item.load_audio(sample_rate=sample_rate)[0]

        fg_track = original_trig.foregrounds[0].model_copy(
            # Use the same config as the trigger foreground, but with the source item being a control
            # and the start/end also updated accordingly
            update={
                "source_item": control_item,
                # Start the control at the same time as the trig, and play it all out
                "start": original_trig.foregrounds[0].start,
                "end": original_trig.foregrounds[0].start + len(control_audio),
            }
        )
        fg_specs = ((fg_track, control_audio),)

        mix, ground_truth = binaural_mix(
            fg_specs=fg_specs,
            bg_specs=bg_specs,
            global_params=global_mixing_params,
            is_trig=False,
        )

        return MisophoniaItem(
            split=split,
            is_trigger=False,
            mix=mix,
            ground_truth=ground_truth,
            length=mix.shape[1],
            global_mixing_params=global_mixing_params,
            foregrounds=(fg_track,),
            backgrounds=bg_tracks,
            paired_uuid=original_trig.uuid,
        )

    pairs_split = MisophoniaDatasetSplit(
        split=split,
        num_samples=len(trig_samples),
        get_one=_get_one,
    )

    original.save_split(pairs_split, if_exists="append", show_progress=True)
