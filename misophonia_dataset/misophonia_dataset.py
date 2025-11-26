from typing import Iterator

import pandas as pd

from misophonia_dataset.interface import SourceData


class MisophoniaDataset:  # TODO: Refactor so we have a Dataset interface that this and SourceData inherit from
    """
    IMPORTANT: The metadata of all SourceData objects passed to MisophoniaData should have a "filename" column and "label"
    column, "isTrig" column, and "split" column
    """

    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        # each source data has a metadata dataframe
        # need to split each df based on "split" and merge into train_df, val_df, test_df
        # each source data also has a path attribute. need to be able to retreive this
        # when we wish to mix clips
        self.train, self.val, self.test = self.split_and_merge()

    def split_and_merge(self) -> list[pd.DataFrame]:
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

    class MisophoniaItem:
        #     component_sounds =
        #     duration
        #     amplitude
        def __init__(self) -> None:
            raise NotImplementedError()
            pass

    def generate(self, batch_size: int, meta: pd.DataFrame, *, display: bool) -> Iterator[MisophoniaItem]:
        raise NotImplementedError()
        for i in range(batch_size):
            continue
