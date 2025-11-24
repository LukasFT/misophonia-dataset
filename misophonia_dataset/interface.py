from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, TypeAlias

import pandera.pandas as pa
import pandera.typing as pat

DEFAULT_DIR = NotImplementedError  # TODO: Refactor!

MappingT: TypeAlias = dict[str, dict[Literal["foams_mapping"], str]]
"""The structure of a mapping from dataset-specific classes to FOAMS classes."""


def get_default_data_dir(*, dataset_name: str | None = None, base_dir: Path | None = None) -> Path:
    base_dir = base_dir or Path(__file__).parent.parent / "data"
    if dataset_name is None:
        return base_dir
    return base_dir / dataset_name


class SourceMetaData(pa.DataFrameModel):
    """The schema for standardized metadata for source datasets."""

    # TODO: Maybe we should do this outside the source datasets, as it all needs to be aligned.
    # split: pat.Series[str] = pa.Field(isin={"train", "val", "test"})
    # """Dataset split: train, val, or test."""

    source_dataset: pat.Series[str] = pa.Field()
    """Name of the source dataset that returned this metadata."""

    file_path: pat.Series[str] = pa.Field()
    """Path to the audio file."""
    freesound_id: pat.Series[int] = pa.Field(nullable=True)
    """FreeSound.org ID of the audio file, if available."""

    trigger_category: pat.Series[str] = pa.Field(nullable=True)
    """Trigger category according to FOAMS taxonomy."""

    licensing: pat.Series[object] = pa.Field(nullable=True)
    """Licensing information. Can be an object or list of objects, e.g.: 
        [{license_url: str, attribution_name: str, attribution_url: str}, ...]
    """


class SourceData(ABC):
    @abstractmethod
    def is_downloaded(self) -> bool:
        """
        Checks if the dataset has already been downloaded.

        Returns:
            True if the dataset is downloaded, False otherwise.
        """
        pass

    @abstractmethod
    def download_data(self) -> None:
        """
        Downloads dataset, extracts it, and saves it into the specified directory.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> SourceMetaData:
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Deletes the entire dataset. Useful after mixing sounds.
        """
        pass

    def __str__(self) -> str:
        return f"<SourceData: {self.__class__.__name__}>"
