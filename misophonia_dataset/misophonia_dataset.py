import os
import uuid
from pathlib import Path
from typing import Iterator, List

import numpy as np
import pandas as pd
import soundfile as sf

from .interface import DEFAULT_MIX_DIR, LicenseT, SourceData, SplitT
from .mixing import MixingParams


class MisophoniaItem:
    def __init__(
        self,
        *,
        mix: np.ndarray,
        ground_truth: np.ndarray,
        mixing_params: MixingParams,
        fg_path: Path,
        bg_path: Path,
        fg_labels: List[str],
        bg_labels: List[str],
        fg_lisence: LicenseT,
        bg_lisence: LicenseT,
        fg_freesound_id: int | None,
        bg_freesound_id: int | None,
        split: SplitT,
    ) -> None:
        self.mix = mix
        self.ground_truth = ground_truth
        self.mixing_params = mixing_params

        self.fg_path = fg_path
        self.bg_path = bg_path
        self.fg_labels = fg_labels
        self.bg_labels = bg_labels

        self.fg_lisence = fg_lisence
        self.bg_lisence = bg_lisence

        self.fg_freesound_id = fg_freesound_id
        self.bg_freesound_id = bg_freesound_id

        self.split = split


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
        self, num_samples: int, *, split: SplitT, random_state: int = 42, to_save: bool
    ) -> Iterator[MisophoniaItem]:
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

        trig_control_df = meta[(meta["label_type"] == "trigger") or (meta["label_type"] == "control")]
        background_df = meta[meta["label_type"] == "background"]
        trig_control_samples = _sample_full_then_restart(trig_control_df, num_samples)
        background_samples = _sample_full_then_restart(background_df, num_samples)

        for trig_control_row, bg_row in zip(trig_control_samples, background_samples):
            params = MixingParams()
            is_trig = True if trig_control_row["label_type"] == "trigger" else False
            (
                mix,
                ground_truth,
                _,
            ) = binaural_mix(trig_control_row["file_path"], bg_row["file_path"], params, is_trig=is_trig)
            miso_item = MisophoniaItem(
                mix=mix,
                ground_truth=ground_truth,
                mixing_params=params,
                fg_path=trig_control_row["file_path"],
                bg_path=bg_row["file_path"],
                fg_labels=trig_control_row["labels"],
                bg_labels=bg_row["labels"],
                fg_lisence=trig_control_row["lisencing"],
                bg_lisence=bg_row["lisencing"],
                fg_freesound_id=trig_control_row["freesound_id"],
                bg_freesound_id=bg_row["freesoun_id"],
                split=SplitT,
            )

            yield miso_item


def save_file(item: MisophoniaItem, split: SplitT, id: uuid.UUID, base_dir: Path = DEFAULT_MIX_DIR) -> tuple[str, str]:
    mix_path = os.path.join(base_dir, str(split), "mix", str(id))
    ground_truth_path = os.path.join(base_dir, str(split), "ground_truth", f"{id}_ground_truth")

    os.makedirs(os.path.dirname(mix_path), exist_ok=True)
    os.makedirs(os.path.dirname(ground_truth_path), exist_ok=True)

    sf.write(mix_path + ".wav", item.mix, item.mixing_params.sr)
    sf.write(ground_truth_path + ".wav", item.ground_truth, item.mixing_params.sr)

    return mix_path + ".wav", ground_truth_path + ".wav"


def generate_miso_dataset(
    dataset: MisophoniaDataset,
    n_samples: int,
    split: SplitT,
) -> pd.DataFrame:
    """
    Generates n_samples of binaural mixes and saves mixes + ground_truths to binaural_data/{split}.
    Should be called to generate a dataset. To generate data on the fly, just call dataset.generate(n_samples, split) and
    proceed accordingly.
    """
    rows = [None] * n_samples
    i = 0
    for item in dataset.generate(num_samples=n_samples, split=split):
        # Save audio
        id = str(uuid.uuid4())
        mix_path, ground_truth_path = save_file(item, split, id)

        # Save metadata
        row = {
            "uuid": id,  # generate a new UUID for each row
            "mix_path": mix_path,
            "ground_truth_path": ground_truth_path,
            "mixing_params": item.mixing_params,  # can store object or convert to dict
            "fg_path": str(item.fg_path),
            "bg_path": str(item.bg_path),
            "fg_labels": item.fg_labels,
            "bg_labels": item.bg_labels,
            "fg_lisence": item.fg_lisence,
            "bg_lisence": item.bg_lisence,
            "fg_freesound_id": item.fg_freesound_id,
            "bg_freesound_id": item.bg_freesound_id,
            "split": item.split,
        }
        rows[i] = row
        i += 1

    df = pd.DataFrame(rows)
    df.to_json("misophonia_dataset.json", orient="records", indent=2)  # TODO: json or csv?

    return df
