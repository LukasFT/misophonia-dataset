import json
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from ..interface import SourceData
from ._splits import train_valid_test_split

MODULE_DIR = Path(__file__).parent  # TODO: Refactor!


class ESC50(SourceData):
    """
    Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
    ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """

    def __init__(self, mapping: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        self.json_path = Path(os.path.join(MODULE_DIR, "esc50-extracted.json"))
        esc50_dir = self.download_data(save_dir)
        self.dir_path = esc50_dir  # for self.delete()
        self.path = os.path.join(esc50_dir, "audio")

        esc50 = self.get_metadata(esc50_dir)
        esc50 = self.get_samples(esc50)
        self.metadata = train_valid_test_split(0.8, 0.2, 0, esc50)

    def download_data(self, save_dir: Path) -> Path:
        """
        Downloads and extracts the ESC50 dataset from github
        Params:
            save_dir (str): directory to save the dataset
        Returns:
            Full path to the dataset
        """

        if os.path.exists(self.json_path):
            print(f"ESC50 dataset has already been downloaded and unzipped at {save_dir}")
            with open(self.json_path, "r") as f:
                data = json.load(f)
                return Path(data["Path"])

        url = "https://github.com/karoldvl/ESC-50/archive/master.zip"

        os.makedirs(save_dir, exist_ok=True)
        local_zip_path = os.path.join(save_dir, "ESC-50.zip")

        response = requests.get(url, stream=True)  # TODO: Why not use our from ._downloading import download_file???
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024 * 1024

        # Stream download to show progress
        if not os.path.exists("esc50-zip.txt"):
            print("Downloading ESC-50 dataset...")
            with (
                open(local_zip_path, "wb") as file,
                tqdm(
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    desc="Downloading",
                    ascii=True,
                ) as bar,
            ):
                for data in response.iter_content(block_size):
                    file.write(data)
                    bar.update(len(data))
        else:
            print("ESC50 has already been downloaded. Proceeding to extraction.")

            with open(os.path.join(MODULE_DIR, "esc50-zip.txt"), "w") as f:
                pass  # track downloading and extraction of dataset

        print("\nUnzipping ESC-50 dataset...")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        extracted_path = os.path.join(save_dir, "ESC-50-master")
        print(f"Dataset downloaded and extracted to: {extracted_path}")

        # In case another class is instantiated but dataset does not need to be redownloaded.
        if os.path.isfile(os.path.join(MODULE_DIR, "esc50-zip.txt")):
            os.rename(os.path.join(MODULE_DIR, "esc50-zip.txt"), self.json_path)
        with open(self.json_path, "w") as f:
            f.dump({"Path": extracted_path, "Meta": os.path.join(extracted_path, "meta", "esc50.csv")}, f, indent=4)

        print("Deleting ESC-50 zip file...")
        os.remove(local_zip_path)
        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Saves the downloaded metadata as a Dataframe

        """
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                data = json.load(f)
                return pd.read_csv(data["Meta"])
        else:
            raise FileNotFoundError("Please download ESC50 dataset first.")

    def get_samples(self, esc50: pd.DataFrame) -> pd.DataFrame:
        # Only keeping metadata for triggers
        trigger_classes = [k for k in self.mapping.keys()]
        esc50_triggers = esc50[esc50["category"].isin(trigger_classes)]

        print("Filtering trigger samples from ESC50...")
        esc50_triggers.loc[:, "category"] = esc50_triggers["category"].apply(
            lambda x: self.mapping[str(x)]["foams_mapping"]
        )
        esc50_triggers = esc50_triggers.rename(columns={"category": "labels"})
        esc50_triggers.loc[:, "isTrig"] = 1

        return esc50_triggers

    def delete(self) -> None:
        shutil.rmtree(self.dir_path)
        shutil.rmtree(self.json_path)

    def __str__(self) -> str:
        return "ESC50 Dataset"
