from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd

DEFAULT_DIR = Path("../data")


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
    def get_metadata(self) -> pd.DataFrame:
        """
        Reads metadata provided with dataset

        Returns:
            DataFrame of metadata
        """
        pass

    @abstractmethod
    def get_samples(self) -> pd.DataFrame:
        """
        Given the dataset taxanomy, a mapping from said taxanomy to trigger/control classes, returns a df including only
        the samples that correspond to trigger/control classes.

        Returns:
            Dataframe of metadata for only samples of interest
        """
        pass

    @abstractmethod
    def train_valid_test_split(self, p0: float, p1: float, p2: float) -> pd.DataFrame:
        """
        Given a dataframe of metadata, adds a "split" column with 0 (train), 1 (validation) or 2 (test) splits.
        Train/valid/test split proportions are p0/p1/p2

        Returns:
            Metadata dataframe with "split" column added
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Deletes the entire dataset. Useful after mixing sounds.
        """
        pass
