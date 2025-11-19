from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, TypeAlias

import pandera

DEFAULT_DIR = NotImplementedError  # TODO: Refactor!

MappingT: TypeAlias = dict[str, dict[Literal["foams_mapping"], str]]
"""The structure of a mapping from dataset-specific classes to FOAMS classes."""


def get_default_data_dir() -> Path:
    return Path(__file__).parent.parent / "data"


class SourceMetaData(pandera.DataFrameModel):
    pass
    # raise NotImplementedError()  # TODO: Define common metadata schema


class SourceData(ABC):
    @abstractmethod
    def download_data(self) -> Path:
        """
        Downloads dataset, extracts it,
        and saves it into the specified directory.

        Returns:
            path to the saved data
        """
        pass

    @abstractmethod
    def get_metadata(self) -> SourceMetaData:
        """
        Reads metadata provided with dataset

        Returns:
            DataFrame of metadata
        """
        pass

    @abstractmethod
    def get_samples(
        self,
    ) -> SourceMetaData:  # TODO: Why should this implementation be different depending on the dataset?
        """
        Given the dataset taxanomy, a mapping from said taxanomy to trigger/control classes, returns a df including only
        the samples that correspond to trigger/control classes.

        Returns:
            Dataframe of metadata for only samples of interest
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Deletes the entire dataset. Useful after mixing sounds.
        """
        pass
