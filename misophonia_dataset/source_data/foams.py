import json
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import requests

from ..interface import SourceData
from ._downloading import download_file
from ._utils import train_valid_test_split

MODULE_DIR = Path(__file__).parent  # TODO: Refactor!


class FOAMS(SourceData):
    """
    Class for FOAMS misophonia trigger sounds. Downloaded from https://zenodo.org/records/7109069
    """

    def __init__(self, save_dir: Path) -> None:
        self.json_path = Path(os.path.join(MODULE_DIR, "foams-extracted.json"))
        self.path = self.download_data(save_dir)

        foams_df = self.get_metadata(self.path)
        self.metadata = train_valid_test_split(0.8, 0.2, 0, foams_df)

    def download_data(self, save_dir: Path) -> Path:
        """
        Download 50 trigger samples from FOAMS at https://zenodo.org/records/7109069/files/. First checks if they have been downloaded alrady.
        Params:
            save_dir
        """
        url = "https://zenodo.org/records/7109069/files/FOAMS_processed_audio.zip?download=1"
        if not os.path.exists(self.json_path):
            unzipped_data = download_file(url, save_dir)

            with zipfile.ZipFile(unzipped_data, "r") as zip_ref:
                zip_ref.extractall(save_dir)

            extracted_path = os.path.join(save_dir, "FOAMS_processed_audio")
            with open(self.json_path, "w") as f:
                json.dump({"Path": extracted_path}, f, indent=4)

            print("Removing FOAMS zip...")
            os.remove(unzipped_data)
        else:
            print("FOAMS dataset has already been downloaded and unzipped.")

        with open(self.json_path, "r") as f:
            data = json.load(f)
            return data["Path"]

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        if not os.path.exists(self.json_path):
            raise FileNotFoundError("Please download FOAMS dataset before getting metadata.")

        with open(self.json_path, "r") as f:
            data = json.load(f)
            if "Meta" in data.keys():
                print("Metadata has already been downloaded.")
                metadata = pd.read_csv(data["Meta"])
                metadata = metadata.rename(columns={"id": "filename", "label": "labels"})
                metadata.loc[:, "isTrig"] = 1
                return metadata
        # otherise download from the web
        url = "https://zenodo.org/record/7109069/files/segmentation_info.csv?download=1"
        response = requests.get(url)
        response.raise_for_status()

        metadata_path = os.path.join(extracted_path, "segmentation_info.csv")
        with open(metadata_path, "wb") as f:
            f.write(response.content)

        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data["Meta"] = metadata_path
            json.dump(data, f, indent=4)

        metadata = pd.read_csv(metadata_path)
        metadata = metadata.rename(columns={"id": "filename", "label": "labels"})
        metadata.loc[:, "isTrig"] = 1
        return metadata

    def get_samples(self) -> pd.DataFrame:
        pass

    def delete(self) -> None:
        shutil.rmtree(self.path)

    def __str__(self) -> str:
        return "FOAMS Dataset"
