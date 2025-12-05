import json
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Iterator, List

import numpy as np
import pandas as pd
import pydantic
import soundfile as sf

from .interface import License, SourceData, SplitT
from .mixing import MixingParams


class MisophoniaItem(pydantic.BaseModel):
    split: SplitT

    mixing_params: MixingParams

    mix: np.ndarray
    ground_truth: np.ndarray | None

    fg_path: Path
    bg_path: Path
    fg_labels: List[str]
    bg_labels: List[str]

    fg_freesound_id: int | None
    bg_freesound_id: int | None

    fg_licensing: tuple[License, ...] | None = None
    bg_licensing: tuple[License, ...] | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)


class MisophoniaDataset:
    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        # each source data has a metadata dataframe
        # need to split each df based on "split" and merge into train_df, val_df, test_df

        self._dfs = self._get_split_dfs()

    def _get_split_dfs(self) -> list[pd.DataFrame]:
        assert all(ds.is_downloaded() for ds in self._source_data), "All source data must be downloaded."
        all_source_data = pd.concat([ds.get_metadata() for ds in self._source_data], ignore_index=True)

        df_by_split = {}
        for split in ["train", "val", "test"]:
            df_by_split[split] = all_source_data[all_source_data["split"] == split]

        assert sum(len(df) for df in df_by_split.values()) == len(all_source_data), "Some samples are missing a split."
        return df_by_split

    def generate(
        self,
        num_samples: int,
        *,
        split: SplitT,
        random_state: int = 42,
    ) -> Generator[MisophoniaItem, None, None]:
        from .mixing import binaural_mix  # Import it here since it requires binamix to be setup

        meta = self._dfs[split]

        def _sample_full_then_restart(df: pd.DataFrame, n: int) -> Iterator[pd.DataFrame]:
            rand_state = random_state
            samples = df.sample(n=min(n, len(df)), random_state=rand_state)
            for i in range(n):
                if i > 0 and i % len(df) == 0:
                    rand_state += 1
                    samples = df.sample(n=min(n, len(df)), random_state=rand_state)
                yield samples.iloc[i % len(df)]

        trig_control_df = meta[meta["label_type"].isin(["trigger", "control"])]
        background_df = meta[meta["label_type"] == "background"]
        trig_control_samples = _sample_full_then_restart(trig_control_df, num_samples)
        background_samples = _sample_full_then_restart(background_df, num_samples)

        for trig_control_row, bg_row in zip(trig_control_samples, background_samples):
            params = MixingParams()  # Intialize random mixing params

            is_trig = trig_control_row["label_type"] == "trigger"

            mix, ground_truth, _ = binaural_mix(
                fg_path=trig_control_row["file_path"],
                bg_path=bg_row["file_path"],
                params=params,
                is_trig=is_trig,
            )

            miso_item = MisophoniaItem(
                split=split,
                mix=mix,
                ground_truth=ground_truth,
                mixing_params=params,
                is_trig=is_trig,
                fg_path=trig_control_row["file_path"],
                bg_path=bg_row["file_path"],
                fg_labels=trig_control_row["labels"],
                bg_labels=bg_row["labels"],
                fg_freesound_id=trig_control_row["freesound_id"],
                bg_freesound_id=bg_row["freesound_id"],
                fg_licensing=trig_control_row["licensing"],
                bg_licensing=bg_row["licensing"],
            )

            yield miso_item


def save_miso_dataset(
    generator: Generator[MisophoniaItem, None, None],
    split: SplitT,
    *,
    base_dir: Path | None = None,
) -> list[dict]:
    rows = []
    license_rows = []  # TODO: implement license saving

    base_dir = base_dir if base_dir is not None else Path(__file__).parent.parent / "data" / "mixed"

    split_dir = base_dir / split
    mix_dir = split_dir / "mixes"
    gt_dir = split_dir / "ground_truths"
    metadata_file = split_dir / "metadata.json"

    if mix_dir.exists() or gt_dir.exists():
        raise FileExistsError(f"Directory for split '{split}' already exists at {base_dir / split}")

    mix_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)

    for item in generator:
        mix_id = str(uuid.uuid4())  # Make unique ID for each mix

        mix_file = mix_dir / f"{mix_id}.wav"
        sf.write(mix_file, np.transpose(item.mix), samplerate=item.mixing_params.sr, subtype="PCM_24")

        if item.ground_truth is not None:
            gt_file = gt_dir / f"{mix_id}.wav"
            sf.write(gt_file, np.transpose(item.ground_truth), samplerate=item.mixing_params.sr, subtype="PCM_24")

        row = {
            "mix_id": mix_id,
            "split": item.split,
            "is_trig": item.is_trig,
            "fg_labels": item.fg_labels,
            "bg_labels": item.bg_labels,
            "fg_freesound_id": item.fg_freesound_id,
            "bg_freesound_id": item.bg_freesound_id,
            "mixing_params": item.mixing_params.model_dump(),
        }
        # TODO: handle licenses
        rows.append(row)

    with metadata_file.open("w") as f:
        json.dump(rows, f, indent=4)

    return rows
