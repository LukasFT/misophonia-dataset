import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

from misophonia_dataset.interface import SourceData

########################### Path of Module ##############################
module_dir = os.path.dirname(__file__)

########################### Utility Functions ###########################


def download_file(url: str, md5: str, save_dir: Path) -> Path:
    """
    Helper function to download large files from the web. Displays progress bar and provides resume support.
    Used primarily for FSD50K and FSD50K_eval datasets.

    Params:
        url (str): url from which to download the file
        save_dir (Path): path to save the file
    Returns:
        the full path of the saved file
    """

    """
    Download a large file with automatic retries and resume support.

    Args:
        url (str): URL of the file.
        save_dir (Path): Directory to save into.
        max_retries (int): Number of retry attempts.
        backoff_factor (float): Exponential backoff multiplier.

    Returns:
        Path: Path to downloaded file.
    """
    max_retries = 5

    # Remove query params
    filename = os.path.basename(urlparse(url).path)
    save_path = Path(save_dir) / filename

    for attempt in range(1, max_retries + 1):
        try:
            # Check for partial file
            headers = {}
            if save_path.exists():
                existing = save_path.stat().st_size
                headers["Range"] = f"bytes={existing}-"
            else:
                existing = 0

            # Request (with streaming)
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0)) + existing
            mode = "ab" if existing else "wb"
            chunk_size = 1024 * 1024  # 1MB

            with (
                open(save_path, mode) as f,
                tqdm(
                    total=total_size,
                    initial=existing,
                    unit="B",
                    unit_scale=True,
                    desc=f"Downloading {filename}",
                    ascii=True,
                ) as bar,
            ):
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

            return Path(save_path)

        except Exception as e:
            print(f"\nError downloading {filename} (attempt {attempt}/{max_retries}): {e}")

            if attempt == max_retries:
                print("Max retries reached — giving up.")
                raise

            # Exponential backoff
            sleep_time = 1.5**attempt
            print(f"Retrying in {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)

    # Check integrity of files
    assert check_md5(Path(save_path), md5)

    # Should never reach here
    return Path(save_path)


def check_md5(file: Path, md5: str) -> bool:
    with open(file, "rb") as f:
        data = f.read()
        md5_hash = hashlib.md5(data).hexdigest()

    return md5_hash == md5


############################ Dataset Classes ###########################


class Dataset(SourceData):
    """Dataset class just for train_valid_test_split method inheritance"""

    def __init__(self) -> None:
        pass

    def download_data(self) -> Path:
        pass

    def get_metadata(self) -> pd.DataFrame:
        pass

    def get_samples(self) -> pd.DataFrame:
        pass

    def train_valid_test_split(self, p0: float, p1: float, p2: float, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates train/valid/test split for dataset based on provided proportions.

        Returns:
            Metadata dataframe with "split" column added
        """
        assert abs(p0 + p1 + p2 - 1.0) < 1e-6, "Proportions must sum to 1."
        print("Creating train/valid/test split...")
        meta = df.copy()
        meta = meta.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle the dataframe
        meta["split"] = np.random.choice([0, 1, 2], size=meta.shape[0], p=[p0, p1, p2])

        return meta

    def delete(self) -> None:
        pass


class ESC50(Dataset):
    """
    Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
    ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """

    def __init__(self, mapping: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        self.json_path = Path(os.path.join(module_dir, "esc50-extracted.json"))
        esc50_dir = self.download_data(save_dir)
        self.dir_path = esc50_dir  # for self.delete()
        self.path = os.path.join(esc50_dir, "audio")

        esc50 = self.get_metadata(esc50_dir)
        esc50 = self.get_samples(esc50)
        self.metadata = self.train_valid_test_split(0.8, 0.2, 0, esc50)

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

        response = requests.get(url, stream=True)
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

            with open(os.path.join(module_dir, "esc50-zip.txt"), "w") as f:
                pass  # track downloading and extraction of dataset

        print("\nUnzipping ESC-50 dataset...")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        extracted_path = os.path.join(save_dir, "ESC-50-master")
        print(f"Dataset downloaded and extracted to: {extracted_path}")

        # In case another class is instantiated but dataset does not need to be redownloaded.
        if os.path.isfile(os.path.join(module_dir, "esc50-zip.txt")):
            os.rename(os.path.join(module_dir, "esc50-zip.txt"), self.json_path)
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


class FSD50K(Dataset):
    """
    Class for the FSD50K dev set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
    When downloading and unzipping the dataset, txt files are generated to track progress.
    Controls, triggers, and backgrounds are sampled from FSD50K.
    """

    def __init__(self, mapping: Path, backgrounds: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        with open(backgrounds, "r") as f:
            self.backgrounds = json.load(f)["Backgrounds"]

        self.json_path = Path(os.path.join(module_dir, "fsd50k-extracted.json"))
        self.path = self.download_data(save_dir)

        fsd50k = self.get_metadata(self.path)
        fsd50k = self.get_samples(fsd50k)
        self.metadata = self.train_valid_test_split(0.8, 0.2, 0, fsd50k)

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

        if not os.path.exists(os.path.join(module_dir, "fsd50k-zip.txt")):
            with ThreadPoolExecutor(max_workers=6) as executor:
                zip_files = list(executor.map(lambda url_hash: download_file(url_hash[0], url_hash[1], save_dir), urls))

            print(zip_files[0])

            with open(os.path.join(module_dir, "fsd50k-zip.txt"), "w"):
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
        if os.path.isfile(os.path.join(module_dir, "fsd50k-zip.txt")):
            os.rename(os.path.join(module_dir, "fsd50k-zip.txt"), self.json_path)
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


class FSD50KEval(Dataset):
    """
    Class for the FSD50K eval set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
    When downloading and unzipping the dataset, txt files are generated to track progress.
    Controls, triggers, and backgrounds are sampled from FSD50K.
    """

    def __init__(self, mapping: Path, backgrounds: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        with open(backgrounds, "r") as f:
            self.backgrounds = json.load(f)["Backgrounds"]

        self.json_path = Path(os.path.join(module_dir, "fsd50k-extracted.json"))
        self.path = self.download_data(save_dir)

        fsd50k_eval = self.get_metadata(self.path)
        fsd50k_eval = self.get_samples(fsd50k_eval)
        self.metadata = self.train_valid_test_split(0, 0, 1.0, fsd50k_eval)

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


class FOAMS(Dataset):
    """
    Class for FOAMS misophonia trigger sounds. Downloaded from https://zenodo.org/records/7109069
    """

    def __init__(self, save_dir: Path) -> None:
        self.json_path = Path(os.path.join(module_dir, "foams-extracted.json"))
        self.path = self.download_data(save_dir)

        foams_df = self.get_metadata(self.path)
        self.metadata = self.train_valid_test_split(0.8, 0.2, 0, foams_df)

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


class MisophoniaData:
    """
    IMPORTANT: The metadata of all SourceData objects passed to MisophoniaData should have a "filename" column and "label"
    column, "isTrig" column, and "split" column
    """

    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        # each source data has a metadata dataframe
        # need to split each df based on "split" and merge into train_df, val_df, test_df
        # each source data also has a path attribute. need to be able to retreive this
        # when we wish to mix clips
        self.train, self.val, self.test = self.split_and_merge()

    def split_and_merge(self) -> list[pd.DataFrame]:
        train_dfs = []
        val_dfs = []
        test_dfs = []

        for src in self._source_data:
            meta = src.metadata[["filename", "labels", "isTrig", "split"]].copy()

            # Add source name or type identifier
            meta["source"] = type(src).__name__

            # Split using the "split" column
            train_dfs.append(meta[meta["split"] == 0])
            val_dfs.append(meta[meta["split"] == 1])
            test_dfs.append(meta[meta["split"] == 2])

        # Concatenate each list; ignore_index for clean reindexing
        train_df = pd.concat(train_dfs, ignore_index=True) if train_dfs else pd.DataFrame()
        val_df = pd.concat(val_dfs, ignore_index=True) if val_dfs else pd.DataFrame()
        test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame()

        return train_df, val_df, test_df

    class MisophoniaItem:
        #     component_sounds =
        #     duration
        #     amplitude
        def __init__(self) -> None:
            pass

    def generate(self, batch_size: int, meta: pd.DataFrame, display: bool) -> Iterator[MisophoniaItem]:
        for i in range(batch_size):
            continue
