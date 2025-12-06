import itertools
import json
import uuid
import warnings
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Iterator

import numpy as np
import soundfile as sf

from .interface import GlobalMixingParams, MisophoniaDataset, MisophoniaItem, SourceData, SourceDataItem, SplitT


class GeneratedMisophoniaDataset(MisophoniaDataset):
    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        # each source data has a metadata dataframe
        # need to split each df based on "split" and merge into train_df, val_df, test_df

        self._items_by_split: dict[SplitT, list[SourceDataItem]] | None = None  # Evaluate lazily

    def iterate(
        self,
        split: SplitT,
        *,
        num_samples: int,
        foregrounds_per_item: tuple[int, int] = (1, 1),
        backgrounds_per_item: tuple[int, int] = (1, 3),
        trig_to_control_ratio: float = 0.5,
        random_seed: int = 42,
    ) -> Generator[MisophoniaItem, None, None]:
        from .mixing import binaural_mix, prepare_track_specs  # Import it here since it requires binamix to be setup

        if split == "test":
            warnings.warn(
                """You are generating a new test dataset that is not the canonical version. """
                """Please do not use this for comparisons across different papers. """
                """See PremadeMisophoniaDataset for loading the canonical test dataset.""",
                UserWarning,
            )

        self.prepare()

        items: list[SourceDataItem] = self._items_by_split[split]

        rng = np.random.default_rng(seed=random_seed)

        def _sample_full_then_restart(subset: list[SourceDataItem]) -> Iterator[SourceDataItem]:
            rand_state = random_seed
            while True:
                samples = subset.copy()
                rng.shuffle(samples)
                rand_state += 1
                for sample in samples:
                    yield sample

        trig_sampler = _sample_full_then_restart([item for item in items if item.label_type == "trigger"])
        control_sampler = _sample_full_then_restart([item for item in items if item.label_type == "control"])
        background_sampler = _sample_full_then_restart([item for item in items if item.label_type == "background"])

        for _ in range(num_samples):
            num_foregrounds = rng.integers(foregrounds_per_item[0], foregrounds_per_item[1] + 1)
            num_backgrounds = rng.integers(backgrounds_per_item[0], backgrounds_per_item[1] + 1)

            is_trig = rng.random() < trig_to_control_ratio
            foreground_samples = trig_sampler if is_trig else control_sampler

            foreground_items = [next(foreground_samples) for _ in range(num_foregrounds)]
            background_items = [next(background_sampler) for _ in range(num_backgrounds)]

            foreground_categories = tuple(set(itertools.chain.from_iterable(item.labels for item in foreground_items)))
            background_categories = tuple(set(itertools.chain.from_iterable(item.labels for item in background_items)))

            global_params = GlobalMixingParams(_rng=rng)  # Initilaze global mixing params at random

            # Load and pre-process audio and initialize SourceTrack params
            foreground_specs, background_specs = prepare_track_specs(
                foreground_items,
                background_items,
                global_params=global_params,
                bg_track_options={"level": 0.7},  # TODO: Why this?
                rng=rng,
            )
            foreground_tracks, _ = tuple(zip(*foreground_specs))  # Take only the first element of each tuple
            background_tracks, _ = tuple(zip(*background_specs))

            mix, ground_truth = binaural_mix(
                fg_tracks=foreground_specs,
                bg_tracks=background_specs,
                global_params=global_params,
                is_trig=is_trig,
            )

            yield MisophoniaItem(
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

    def prepare(self) -> None:
        if self._items_by_split is not None:
            return

        assert all(ds.is_downloaded() for ds in self._source_data), "All source data must be downloaded."

        # Get a list of all source data items from all source datasets
        all_source_data = tuple(itertools.chain.from_iterable([ds.get_metadata() for ds in self._source_data]))

        # Split source data items by split
        items_by_split: dict[SplitT, list[SourceDataItem]] = {"train": [], "val": [], "test": []}
        for item in all_source_data:
            items_by_split[item.split].append(item)

        self._items_by_split = items_by_split


class PremadeMisophoniaDataset(MisophoniaDataset):
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)

        self._items_by_split: dict[SplitT, list[MisophoniaItem]] | None = None

    def prepare(self) -> None:
        if self._items_by_split is not None:
            return

        self._items_by_split = {"train": [], "val": [], "test": []}

        cwd = Path.cwd()

        for split in self._items_by_split.keys():
            split_dir = (self.base_dir / split).resolve().relative_to(cwd)
            metadata_file = split_dir / "metadata.jsonl"

            if not metadata_file.exists():
                # Allow missing splits (e.g. only train/val present)
                self._items_by_split[split] = None
                continue

            with metadata_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line == "":
                        continue

                    obj = json.loads(line)
                    obj["mix"] = split_dir / obj["mix"]
                    obj["ground_truth"] = split_dir / obj["ground_truth"] if obj["ground_truth"] is not None else None
                    item = MisophoniaItem.model_validate(obj)
                    self._items_by_split[split].append(item)

    def iterate(self, split: SplitT) -> Iterable[MisophoniaItem]:
        self.prepare()

        if self._items_by_split[split] is None:
            raise ValueError(f"No data available for split '{split}'")

        for item in self._items_by_split[split]:
            yield item


def save_miso_dataset(
    items: Iterable[MisophoniaItem],
    split: SplitT,
    *,
    base_dir: Path | None = None,
) -> None:
    base_dir = base_dir if base_dir is not None else Path(__file__).parent.parent / "data" / "mixed"

    split_dir = base_dir / split
    mix_dir = split_dir / "mixes"
    gt_dir = split_dir / "ground_truths"
    metadata_file = split_dir / "metadata.jsonl"

    if split_dir.exists():
        raise FileExistsError(f"Directory for split '{split}' already exists at {split_dir}")

    mix_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)

    with metadata_file.open("w", buffering=1) as metadata_f:  # buffer=1 means flush on newline
        for item in items:
            mix_id = str(uuid.uuid4())  # Make unique ID for each mix

            mix_file = mix_dir / f"{mix_id}.wav"
            sf.write(
                mix_file, np.transpose(item.mix), samplerate=item.global_mixing_params.sample_rate, subtype="PCM_24"
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

            item = item.model_copy(
                update={
                    "uuid": mix_id,
                    "mix": mix_file.relative_to(split_dir),
                    "ground_truth": gt_file.relative_to(split_dir) if gt_file is not None else None,
                }
            )
            row = item.model_dump_json(round_trip=True)
            metadata_f.write(row + "\n")
