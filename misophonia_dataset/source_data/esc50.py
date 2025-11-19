import json
import os
from pathlib import Path

import pandas as pd

from ..interface import MappingT, SourceData, get_default_data_dir
from ._utils import train_valid_test_split


class ESC50(SourceData):
    """
    Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
    ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """

    def __init__(self, *, save_dir: Path | None = None, mapping: None | MappingT = None) -> None:
        if mapping is None:
            with (Path(__file__).parent / "esc50_mapping.json").open("r") as f:
                mapping = json.load(f)
        self.mapping = mapping

        self._dir_path = save_dir if save_dir is not None else get_default_data_dir() / "ESC50"

        esc50 = self.get_metadata()
        esc50 = self.get_samples(esc50)
        self.metadata = train_valid_test_split(0.8, 0.2, 0, esc50)

    def download_data(self) -> Path:
        """
        Downloads and extracts the ESC50 dataset from github
        Params:
            save_dir (str): directory to save the dataset
        Returns:
            Full path to the dataset
        """

        state_json = self._dir_path / "state_esc50.json"
        if state_json.exists():
            print(f"ESC50 dataset has already been downloaded and unzipped at {self._dir_path}")
            with state_json.open("r") as f:
                data = json.load(f)
                return Path(data["Path"])

        raise NotImplementedError("Need to refactor downloading code to use download_file from ._downloading.py")
        # url = "https://github.com/karoldvl/ESC-50/archive/master.zip"

        # os.makedirs(self._dir_path, exist_ok=True)
        # local_zip_path = os.path.join(self._dir_path, "ESC-50.zip")

        # response = requests.get(url, stream=True)  # TODO: Why not use our from ._downloading import download_file???
        # response.raise_for_status()

        # total_size = int(response.headers.get("content-length", 0))
        # block_size = 1024 * 1024

        # # Stream download to show progress
        # if not os.path.exists("esc50-zip.txt"):
        #     print("Downloading ESC-50 dataset...")
        #     with (
        #         open(local_zip_path, "wb") as file,
        #         tqdm(
        #             total=total_size,
        #             unit="iB",
        #             unit_scale=True,
        #             desc="Downloading",
        #             ascii=True,
        #         ) as bar,
        #     ):
        #         for data in response.iter_content(block_size):
        #             file.write(data)
        #             bar.update(len(data))
        # else:
        #     print("ESC50 has already been downloaded. Proceeding to extraction.")

        #     with open(os.path.join(DATA_DIR, "esc50-zip.txt"), "w") as f:
        #         pass  # track downloading and extraction of dataset

        # print("\nUnzipping ESC-50 dataset...")
        # with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
        #     zip_ref.extractall(save_dir)

        # extracted_path = os.path.join(save_dir, "ESC-50-master")
        # print(f"Dataset downloaded and extracted to: {extracted_path}")

        # # In case another class is instantiated but dataset does not need to be redownloaded.
        # if os.path.isfile(os.path.join(DATA_DIR, "esc50-zip.txt")):
        #     os.rename(os.path.join(DATA_DIR, "esc50-zip.txt"), self.json_path)
        # with open(self.json_path, "w") as f:
        #     f.dump({"Path": extracted_path, "Meta": os.path.join(extracted_path, "meta", "esc50.csv")}, f, indent=4)

        # print("Deleting ESC-50 zip file...")
        # os.remove(local_zip_path)
        # return Path(extracted_path)

    def get_metadata(self) -> pd.DataFrame:
        """
        Saves the downloaded metadata as a Dataframe

        """
        raise NotImplementedError("Need to refactor with the file paths!")
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                data = json.load(f)
                return pd.read_csv(data["Meta"])
        else:
            raise FileNotFoundError("Please call .download_data() before getting metadata.")

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
        self._dir_path.rmdir()

    def __str__(self) -> str:
        return "ESC50 Dataset"
