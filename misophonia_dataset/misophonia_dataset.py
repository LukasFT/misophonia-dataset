import os
from typing import Iterator

import numpy as np
import pandas as pd

from .interface import SourceData
from .mixing import binaural_mix


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

        self._train, self._val, self._test = self._get_split_dfs()
        self.paths = {type(s).__name__: s.path for s in source_data}

    def _get_split_dfs(self) -> list[pd.DataFrame]:
        assert all(ds.is_downloaded() for ds in self._source_data), "All source data must be downloaded."
        all_source_data = pd.concat([ds.get_metadata() for ds in self._source_data], ignore_index=True)
        raise NotImplementedError()
        train_dfs = []
        val_dfs = []
        test_dfs = []

        for src in self._source_data:
            meta = src.metadata[["filename", "labels", "isTrig", "split"]].copy()

            # Add source name or type identifier
            meta["source"] = type(src).__name__

            # Split using the "split" column
            train_dfs.append(meta[meta["split"] == 0])
            val_dfs.append(meta[meta["split"] == 1])
            test_dfs.append(meta[meta["split"] == 2])

        # Concatenate each list; ignore_index for clean reindexing
        train_df = pd.concat(train_dfs, ignore_index=True) if train_dfs else pd.DataFrame()
        val_df = pd.concat(val_dfs, ignore_index=True) if val_dfs else pd.DataFrame()
        test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame()

        return train_df, val_df, test_df

    def generate(self, batch_size: int, meta: pd.DataFrame, show: bool) -> Iterator[MisophoniaItem]:
        trigs_df = meta[meta["isTrig"] == 1]
        background_df = meta[meta["isTrig"] == 2]

        replace = True
        if batch_size > trigs_df.shape[0] or batch_size > background_df.shape[0]:
            replace = False

        trig_samples = trigs_df.sample(n=batch_size, replace=replace, ignore_index=True, random_state=42)
        background_samples = background_df.sample(n=batch_size, replace=replace, ignore_index=True, random_state=42)

        for i in range(batch_size):
            trig_path = os.path.join(
                self.paths[trig_samples.iloc[i]["source"]], str(trig_samples.iloc[i]["filename"]) + ".wav"
            )
            bg_path = os.path.join(
                self.paths[background_samples.iloc[i]["source"]], str(background_samples.iloc[i]["filename"]) + ".wav"
            )

            mix, sr = binaural_mix(trig_path, bg_path)
            yield MisophoniaItem(audio=mix, sr=sr)
