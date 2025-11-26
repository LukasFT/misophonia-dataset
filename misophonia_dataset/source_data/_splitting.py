import hashlib
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from .foams import FoamsDataset
    from .fsd50k import Fsd50kDataset


def is_validated_ids(
    target_freesound_ids: pd.Series,
    *,
    foams: Optional["FoamsDataset"] = None,
) -> pd.Series:
    from .foams import FoamsDataset

    foams = foams or FoamsDataset()
    foams.download_metadata()
    foams_freesound_ids = foams.get_all_sound_ids().to_numpy()

    validated_ids = target_freesound_ids.apply(lambda x: ("FOAMS",) if x in foams_freesound_ids else None)
    return validated_ids


def train_valid_test_split(
    target_freesound_ids: pd.Series,
    *,
    validated_by: pd.Series,
    fsd50k: Optional["Fsd50kDataset"] = None,
    target_val_pct: int = 10,
) -> pd.Series:
    """
    Creates train/valid/test split for the target_metadata.

    In this priority:
    1. If validated (by FOAMS), assign to test
    2. Use FSD50K split if available -- but split into train/val using hashing
    3. Hashing function based on FreeSound.org ID

    Args:
        target_freesound_ids: Series of FreeSound.org IDs to split
        fsd50k: FSD50K dataset instance to use for splitting (optional)
        validated_by: Series indicating which sounds are validated (e.g., by FOAMS)
        target_val_pct: Target validation set ratio (percentage) in terms of 20% test / target_val_pct % val / rest train split.
                            Note that this is not exact due to hashing-based splitting.
                            There is a fixed test size, to ensure we always have the same test set.

    Returns:
        Series of split assignments ("train", "val", "test") for each FreeSound.org ID in target_freesound_ids

    """
    from .fsd50k import Fsd50kDataset

    fsd50k = fsd50k or Fsd50kDataset()

    fsd50k.download_metadata()
    fsd50k_splits = fsd50k.get_original_splits().set_index("freesound_id")
    fsd50k_id_to_split = fsd50k_splits["fsd50k_split"]
    fsd50k_freesound_ids = fsd50k_splits.index.to_numpy()

    assert set(validated_by.index) == set(target_freesound_ids.index), (
        "validated_by index must match target_freesound_ids index"
    )
    is_validated = target_freesound_ids[validated_by.notna()].to_numpy()

    # Use ints to ensure numerical stability
    approx_split_size = {"test": 20}
    approx_split_size["val"] = int(target_val_pct)
    approx_split_size["train"] = 100 - approx_split_size["test"] - approx_split_size["val"]

    # cutoffs between 0-100
    test_cutoff = approx_split_size["test"]  # between 0-100
    val_cutoff = (  # between 0-100, on the second scale (i.e., after test)
        approx_split_size["val"] * 100 // (approx_split_size["val"] + approx_split_size["train"])
    )

    def _get_hash_val(freesound_id: int) -> int:
        hash_value = hashlib.md5(str(freesound_id).encode("utf-8")).hexdigest()
        hash_value = int(hash_value, 16) % 100  # Make to 0-100 range
        # assert 0 <= hash_value < 100
        return hash_value

    def _hash_test_train_val_split(freesound_id: int) -> str:
        hash_value = _get_hash_val(freesound_id)
        if hash_value < test_cutoff:
            return "test"
        # Normalize to 0-100 range after test
        hash_value_0_to_100 = (hash_value - test_cutoff) * 100 // (100 - test_cutoff)
        return _hash_train_val_split(hash_value_0_to_100=hash_value_0_to_100)

    def _hash_train_val_split(*, freesound_id: int | None = None, hash_value_0_to_100: int | None = None) -> str:
        hash_value = (
            hash_value_0_to_100 if hash_value_0_to_100 is not None else _get_hash_val(freesound_id=freesound_id)
        )
        if hash_value < val_cutoff:
            return "val"
        else:
            return "train"

    def _get_fsd50k_split(freesound_id: int) -> Optional[str]:
        if freesound_id in fsd50k_freesound_ids:
            original_split = fsd50k_id_to_split.loc[freesound_id]
            if original_split == "eval":
                return "test"
            else:  # if not train, use hashing to split into train/val
                return _hash_train_val_split(freesound_id=freesound_id)
        return None

    def _test_if_validated(freesound_id: int) -> Optional[str]:
        if freesound_id in is_validated:
            return "test"
        return None

    def _get_final_split(freesound_id: int) -> str:
        # (Priority 1) If validated (e.g., by FOAMS), assign to test
        split = _test_if_validated(freesound_id)
        if split is not None:
            return split

        # (Priority 2) Use FSD50K split if available -- but split into train/val using hashing
        split = _get_fsd50k_split(freesound_id)
        if split is not None:
            return split

        # (Priority 3) Hashing function on (FreeSound.org ID)
        return _hash_test_train_val_split(freesound_id)

    splits = target_freesound_ids.apply(_get_final_split)
    return splits
