import numpy as np
import pandas as pd


def train_valid_test_split(
    p0: float, p1: float, p2: float, df: pd.DataFrame
) -> pd.DataFrame:  # TODO: Do not do this at runtime every time!
    """
    Creates train/valid/test split for dataset based on provided proportions.

    Returns:
        Metadata dataframe with "split" column added
    """
    assert abs(p0 + p1 + p2 - 1.0) < 1e-6, "Proportions must sum to 1."
    print("Creating train/valid/test split...")
    meta = df.copy()
    meta = meta.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle the dataframe
    meta["split"] = np.random.choice(  # noqa: NPY002 FIXME: Use propper RNG syntax
        [0, 1, 2], size=meta.shape[0], p=[p0, p1, p2]
    )

    return meta
