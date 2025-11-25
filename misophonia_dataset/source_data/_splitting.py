from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from misophonia_dataset.source_data.foams import FoamsDataset
    from misophonia_dataset.source_data.fsd50k import Fsd50kDataset


def train_valid_test_split(
    dataset_metadata: pd.DataFrame,
    *,
    fsd_50k: Optional["Fsd50kDataset"] = None,
    foams: Optional["FoamsDataset"] = None,
) -> pd.DataFrame:  # TODO: Do not do this at runtime every time!
    """
    Creates train/valid/test split for dataset based on provided proportions.

    Returns:
        Metadata dataframe with "split" column added
    """
    raise NotImplementedError()

    # approx_split_size = {
    #     "test": 0.2,
    #     "val": 0.1,
    #     "train": 0.7,
    # }

    # (A) Use FSD50K split if available -- but split into train/val using hashing

    # (B) Foams = in test

    # (C) Hashing function on (FreeSound.org ID)
