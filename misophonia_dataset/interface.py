from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, TypeAlias

import pandas as pd
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
    filename: pat.Series[Path]
    pass
    # raise NotImplementedError()  # TODO: Define common metadata schema


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
    def get_samples(self) -> SourceMetaData:
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Deletes the entire dataset. Useful after mixing sounds.
        """
        pass

    def __str__(self) -> str:
        return f"<SourceData: {self.__class__.__name__}>"
