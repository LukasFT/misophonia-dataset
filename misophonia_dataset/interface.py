from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, TypeAlias

import pandera.pandas as pa
import pandera.typing as pat
import pydantic

MappingT: TypeAlias = dict[str, dict[Literal["foams_mapping"], str]]
"""The structure of a mapping from dataset-specific classes to FOAMS classes."""


SplitT: TypeAlias = Literal["train", "val", "test"]
"""The possible dataset splits."""


class License(pydantic.BaseModel):
    license_url: str
    attribution_name: str
    attribution_url: str


def get_default_data_dir(*, dataset_name: str | None = None, base_dir: Path | None = None) -> Path:
    base_dir = base_dir or Path(__file__).parent.parent / "data"
    if dataset_name is None:
        return base_dir
    return base_dir / dataset_name


class SourceMetaData(pa.DataFrameModel):
    """The schema for standardized metadata for source datasets."""

    source_dataset: pat.Series[str] = pa.Field()
    """Name of the source dataset that returned this metadata."""

    split: pat.Series[str] = pa.Field(isin={"train", "val", "test"})
    """Dataset split: train, val, or test. See SplitT."""

    file_path: pat.Series[str] = pa.Field()
    """Path to the audio file."""
    freesound_id: pat.Series[int] = pa.Field(nullable=True)
    """FreeSound.org ID of the audio file, if available."""

    label_type: pat.Series[str] = pa.Field(isin={"control", "trigger", "background"})
    """Type of sound."""
    labels: pat.Series[object] = pa.Field()
    """
    Label according to the FOAMS taxonomy (if sound_type = 'trigger') and, otherwise, the AudioSet (FSD50K) taxonomy.
    
    There can be one more more labels (str or list of str). But all labels must be of the same sound_type. Any data point that has labels from multiple sound_types should be excluded.
    """

    validated_by: pat.Series[object] = pa.Field(nullable=True)
    """List of names for studies (e.g., FOAMS) that have validated this data point. If not any, None. Only applicable for trigger sounds."""

    licensing: pat.Series[object] = pa.Field(nullable=True)
    """Licensing information. A collection of dictionaries (see LicenceT above)."""


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
