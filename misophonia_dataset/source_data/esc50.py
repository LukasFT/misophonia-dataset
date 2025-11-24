import json
import os
from pathlib import Path

import pandas as pd

from ..interface import MappingT, SourceData, SourceMetaData, get_default_data_dir
from ._downloading import download_file, is_unzipped


class Esc50Dataset(SourceData):
    """
    Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
    ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """

    def __init__(self, *, save_dir: Path | None = None, mapping: None | MappingT = None) -> None:
        if mapping is None:
            with (Path(__file__).parent / "esc50_mapping.json").open("r") as f:
                mapping = json.load(f)

        self.mapping: MappingT = mapping

        self._base_save_dir = save_dir if save_dir is not None else get_default_data_dir(dataset_name="ESC50")
        self._base_unzipped_dir = self._base_save_dir / "ESC-50-master"

        # esc50 = self.get_metadata()
        # esc50 = self.get_samples(esc50)
        # self.metadata = train_valid_test_split(0.8, 0.2, 0, esc50)

    def is_downloaded(self) -> bool:
        return is_unzipped(self._base_save_dir / "ESC-50-master.zip")

    def download_data(self) -> None:
        """
        Downloads and extracts the ESC50 dataset from github

        Params:
            save_dir (str): directory to save the dataset

        """
        download_file(
            url="https://github.com/karolpiczak/ESC-50/archive/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6.zip",  # Latest commit per November 24, 2025
            save_dir=self._base_save_dir,
            md5="071b44018315e034b2c6e8064543d19c",
            filename="ESC-50-master.zip",
            unzip=True,
            delete_zip=True,
            rename_extracted_dir=self._base_unzipped_dir.name,
        )

    def get_samples(self) -> SourceMetaData:
        """
        Get standardized metadata for ESC50 dataset.
        """
        assert self.is_downloaded(), "Dataset is not downloaded yet."
        esc50 = pd.read_csv(self._base_unzipped_dir / "meta" / "esc50.csv")
        SourceMetaData.validate(esc50)
        return esc50

        # # Only keeping metadata for triggers
        # trigger_classes = [k for k in self.mapping.keys()]
        # esc50_triggers = esc50[esc50["category"].isin(trigger_classes)]

        # print("Filtering trigger samples from ESC50...")
        # esc50_triggers.loc[:, "category"] = esc50_triggers["category"].apply(
        #     lambda x: self.mapping[str(x)]["foams_mapping"]
        # )
        # esc50_triggers = esc50_triggers.rename(columns={"category": "labels"})
        # esc50_triggers.loc[:, "isTrig"] = 1

        # return esc50_triggers

    def delete(self) -> None:
        self._base_save_dir.rmdir()
