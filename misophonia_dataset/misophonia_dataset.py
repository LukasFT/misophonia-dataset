import os
from typing import Iterator

import numpy as np
import pandas as pd

from .interface import SourceData, SplitT


class MisophoniaItem:
    #     component_sounds =
    #     duration
    #     amplitude
    def __init__(self, audio: np.ndarray, sr: int) -> None:
        self.audio = audio
        self.sr = sr
        # TODO: Add metadata that tracks labels of each component, and origin files


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

    def generate(self, num_samples: int, *, split: SplitT, random_state: int = 42) -> Iterator[MisophoniaItem]:
        try:
            from .mixing import binaural_mix  # Import it here since it requires binamix to be setup
        except Exception as e:
            # TODO: Remove this exception handling when SADIE issue is resolved
            print("Error importing binaural_mix:", e)
            print("Continuing for the demo")

            def binaural_mix(fg: os.PathLike, bg: os.PathLike) -> tuple[np.ndarray, int]:
                print(f"Mixing {fg} and {bg} (dummy function)")
                return None, None

        meta = self._dfs[split]

        trigs_df = meta[meta["label_type"] == "trigger"]
        background_df = meta[meta["label_type"] == "background"]

        def _sample_full_then_restart(df: pd.DataFrame, n: int) -> Iterator[pd.DataFrame]:
            rand_state = random_state
            samples = df.sample(n=min(n, len(df)), random_state=rand_state)
            for i in range(n):
                if i > 0 and i % len(df) == 0:
                    rand_state += 1
                    samples = df.sample(n=min(n, len(df)), random_state=rand_state)
                yield samples.iloc[i % len(df)]

        trigs_df = meta[meta["label_type"] == "trigger"]
        background_df = meta[meta["label_type"] == "background"]
        trig_samples = _sample_full_then_restart(trigs_df, num_samples)
        background_samples = _sample_full_then_restart(background_df, num_samples)

        for trig_row, bg_row in zip(trig_samples, background_samples):
            mix, sr = binaural_mix(trig_row["file_path"], bg_row["file_path"])
            yield MisophoniaItem(audio=mix, sr=sr)
