import json
import os
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from ..interface import SourceData
from ._downloading import download_file
from ._utils import train_valid_test_split

MODULE_DIR = Path(__file__).parent  # TODO: Refactor!


class FSD50K(SourceData):
    """
    Class for the FSD50K dev set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
    When downloading and unzipping the dataset, txt files are generated to track progress.
    Controls, triggers, and backgrounds are sampled from FSD50K.
    """

    def __init__(self, mapping: Path, backgrounds: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        with open(backgrounds, "r") as f:
            self.backgrounds = json.load(f)

        self.json_path = Path(os.path.join(MODULE_DIR, "fsd50k-extracted.json"))
        self.path = self.download_data(save_dir)

        fsd50k = self.get_metadata(self.path)
        fsd50k = self.get_samples(fsd50k)
        self.metadata = train_valid_test_split(0.8, 0.2, 0, fsd50k)

    def download_data(self, save_dir: Path) -> Path:
        """
        Downloads, combines, and extracts FSD50K dataset from Zenodo using multiple threads, with resume support.
        Params:
            save_dir (Path): Path to save the dataset
        Returns:
            full path of saved dataset
        """
        if os.path.exists(self.json_path):
            print(f"FSD50K dataset has already been downloaded and unzipped at {save_dir}")
            with open(self.json_path, "r") as f:
                data = json.load(f)
                return data["Path"]

        urls = [
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.zip?download=1",
                "c480d119b8f7a7e32fdb58f3ea4d6c5a ",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z01?download=1",
                "faa7cf4cc076fc34a44a479a5ed862a3",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z02?download=1",
                "8f9b66153e68571164fb1315d00bc7bc",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z03?download=1",
                "1196ef47d267a993d30fa98af54b7159",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z04?download=1",
                "d088ac4e11ba53daf9f7574c11cccac9",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z05?download=1",
                "81356521aa159accd3c35de22da28c7f ",
            ),
        ]

        os.makedirs(save_dir, exist_ok=True)

        if not os.path.exists(os.path.join(MODULE_DIR, "fsd50k-zip.txt")):
            with ThreadPoolExecutor(max_workers=6) as executor:
                zip_files = list(executor.map(lambda url_hash: download_file(url_hash[0], url_hash[1], save_dir), urls))

            print(zip_files[0])

            with open(os.path.join(MODULE_DIR, "fsd50k-zip.txt"), "w"):
                pass  # to track zip + extraction progress
        else:
            print("FSD50K dataset has already been downloaded. Proceeding to extraction.")

        print("\nUnzipping FSD50K dataset...")
        subprocess.run(["7z", "x", zip_files[0], f"-o{save_dir}"], check=True)

        # First remove component zip files
        for file in zip_files:
            os.remove(file)

        extracted_path = os.path.join(save_dir, "FSD50K.dev_audio")

        # Save the dataset path to a JSON in case a new FSD50K class is made and dataset is present
        if os.path.isfile(os.path.join(MODULE_DIR, "fsd50k-zip.txt")):
            os.rename(os.path.join(MODULE_DIR, "fsd50k-zip.txt"), self.json_path)
        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data["Path"] = extracted_path
            json.dump(data, f, indent=4)

        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Downloads FSD50K metadata from zenodo and saves as a dataframe.

        """
        # Check if metadata has already been downloaded
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                data = json.load(f)
                if "Meta" in data.keys():
                    return pd.read_csv(data["Meta"])
        else:
            raise FileNotFoundError("Please download dataset before downloading the metadata.")

        # Download metadata folder
        url = "https://zenodo.org/records/4060432/files/FSD50K.metadata.zip?download=1"
        md5 = "b9ea0c829a411c1d42adb9da539ed237"
        unzipped_meta = download_file(url, md5, extracted_path)

        # Extract all to FSD50K.dev_audio folder
        with zipfile.ZipFile(unzipped_meta, "r") as zip_ref:
            zip_ref.extractall(extracted_path)

        # Remove zip file
        os.remove(unzipped_meta)

        metadata_path = os.path.join(extracted_path, "FSD50K.metadata", "collection", "collection_dev.csv")

        # Save metadata path so that if new class is instantiated metadata can easily be retrieved.
        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data["Meta"] = metadata_path
            json.dump(data, f, indent=4)

        return pd.read_csv(metadata_path)

    def get_samples(self, fsd50k: pd.DataFrame) -> pd.DataFrame:
        """
        Collects triggers, controls, backgrounds from full FSD50K.dev set using predefined class mappings.
        Removes all unused sound samples.
        Params:
            fsd50k (dataframe): full metadata for dataset
        Returns:
            new metadata dataframe including only the collected sound samples.
        """
        trigger_classes = [k for k in self.mapping["Trigger"].keys()]
        control_classes = [k for k in self.mapping["Control"].keys()]

        conditions = [
            fsd50k["labels"].isin(control_classes),
            fsd50k["labels"].isin(trigger_classes),
            fsd50k["labels"].isin(self.backgrounds),
        ]
        choices = [0, 1, 2]

        # Only keep rows of collected samples
        fsd50k["isTrig"] = np.select(conditions, choices, default=-1)
        fsd50k = fsd50k[fsd50k["isTrig"] >= int(0)].copy()

        # Update label mapping only for Trigger rows
        fsd50k.loc[fsd50k["isTrig"] == 1, "labels"] = fsd50k.loc[fsd50k["isTrig"] == 1, "labels"].apply(
            lambda x: self.mapping["Trigger"][str(x)]["foams_mapping"]
        )

        # Fix rename syntax
        fsd50k = fsd50k.rename(columns={"fname": "filename"})

        return fsd50k

    def delete(self) -> None:
        shutil.rmtree(self.path)
        shutil.rmtree(self.json_path)

    def __str__(self) -> str:
        return "FSDK50 Dataset"


class FSD50KEval(SourceData):
    """
    Class for the FSD50K eval set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
    When downloading and unzipping the dataset, txt files are generated to track progress.
    Controls, triggers, and backgrounds are sampled from FSD50K.
    """

    def __init__(self, mapping: Path, backgrounds: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        with open(backgrounds, "r") as f:
            self.backgrounds = json.load(f)

        self.json_path = Path(os.path.join(MODULE_DIR, "fsd50k-extracted.json"))
        self.path = self.download_data(save_dir)

        fsd50k_eval = self.get_metadata(self.path)
        fsd50k_eval = self.get_samples(fsd50k_eval)
        self.metadata = train_valid_test_split(0, 0, 1.0, fsd50k_eval)

    def download_data(self, save_dir: Path) -> Path:
        """
        Downloads, combines, and extracts FSD50K eval dataset from Zenodo using multiple threads, with resume support.
        Params:
            save_dir (Path): Path to save the dataset
        Returns:
            full path of saved dataset
        """
        # FSD50K eval requires FSD50K dev to be downloaded first, particularly for metadata.
        if not os.path.exists(self.json_path):
            raise FileNotFoundError("Please download FSD50K dev dataset before downloading the eval dataset.")

        with open(self.json_path, "r") as f:
            data = json.load(f)
            if "evalPath" in data.keys():
                print(f"FSD50K eval dataset has already been downloaded and unzipped at {save_dir}")
                return data["evalPath"]

        urls = [
            (
                "https://zenodo.org/records/4060432/files/FSD50K.eval_audio.zip?download=1",
                "6fa47636c3a3ad5c7dfeba99f2637982",
            ),
            (
                "https://zenodo.org/records/4060432/files/FSD50K.eval_audio.z01?download=1",
                "3090670eaeecc013ca1ff84fe4442aeb ",
            ),
        ]

        os.makedirs(save_dir, exist_ok=True)

        if not os.path.exists("fsd50k-eval-zip.txt"):
            with ThreadPoolExecutor(max_workers=2) as executor:
                zip_files = list(executor.map(lambda url_hash: download_file(url_hash[0], url_hash[1], save_dir), urls))

            print(zip_files[0])

            with open("fsd50k-eval-zip.txt", "w") as f:
                pass  # to track zip + extraction progress
        else:
            print("FSD50K eval dataset has already been downloaded. Proceeding to extraction.")

        print("\nUnzipping FSD50K eval dataset...")
        subprocess.run(["7z", "x", zip_files[0], f"-o{save_dir}"], check=True)

        # First remove component zip files
        for file in zip_files:
            os.remove(file)

        extracted_path = os.path.join(save_dir, "FSD50K.eval_audio")

        # Save the dataset path to a JSON in case a new FSD50K_eval class is made and dataset is present
        if os.path.isfile("fsd50k-eval-zip.txt"):
            os.remove("fsd50k-eval-zip.txt")

        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data["evalPath"] = extracted_path
            json.dump(data, f, indent=4)

        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Downloads FSD50K eval metadata from zenodo and saves as a dataframe.

        """
        # Check if metadata has already been downloaded
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                data = json.load(f)
                if "evalMeta" in data.keys():
                    return pd.read_csv(data["evalMeta"])
        else:
            raise FileNotFoundError("Please download FSD50K dev dataset before downloading the eval metadata.")

        metadata_path = os.path.join(extracted_path, "FSD50K.metadata", "collection", "collection_eval.csv")

        # Save metadata path so that if new class is instantiated metadata can easily be retrieved.
        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data["evalMeta"] = metadata_path
            json.dump(data, f, indent=4)

        return pd.read_csv(metadata_path)

    def get_samples(self, fsd50k_eval: pd.DataFrame) -> pd.DataFrame:
        """
        Collects triggers, controls, backgrounds from full FSD50K.eval set using predefined class mappings.
        Removes all unused sound samples.
        Params:
            fsd50k_eval (dataframe): full metadata for dataset
        Returns:
            new metadata dataframe including only the collected sound samples.
        """
        trigger_classes = [k for k in self.mapping["Trigger"].keys()]
        control_classes = [k for k in self.mapping["Control"].keys()]

        conditions = [
            fsd50k_eval["labels"].isin(control_classes),
            fsd50k_eval["labels"].isin(trigger_classes),
            fsd50k_eval["labels"].isin(self.backgrounds),
        ]
        choices = [0, 1, 2]

        # Only keep rows of collected samples
        fsd50k_eval["isTrig"] = np.select(conditions, choices, default=-1)
        fsd50k_eval = fsd50k_eval[fsd50k_eval["isTrig"] >= int(0)].copy()

        # Update label mapping only for Trigger rows
        fsd50k_eval.loc[fsd50k_eval["isTrig"] == 1, "labels"] = fsd50k_eval.loc[
            fsd50k_eval["isTrig"] == 1, "labels"
        ].apply(lambda x: self.mapping["Trigger"][str(x)]["foams_mapping"])

        # Fix rename syntax
        fsd50k_eval = fsd50k_eval.rename(columns={"fname": "filename"})

        return fsd50k_eval

    def delete(self) -> None:
        shutil.rmtree(self.path)

    def __str__(self) -> str:
        return "FSDK50 Eval Dataset"
