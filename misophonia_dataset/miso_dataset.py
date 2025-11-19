import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from interface import DEFAULT_DIR, SourceData
from tqdm import tqdm


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


def merge_zip_files(zip_files: list[Path], save_dir: Path) -> Path:
    """
    Helper function to merge zip component files into one large zip. Primarily used for FSD50K and FSD50K_eval datasets.
    """
    unsplit_zip = os.path.join(save_dir, "unsplit.zip")

    with zipfile.ZipFile(unsplit_zip, "w", compression=zipfile.ZIP_DEFLATED) as merged_zip:
        for zip_path in zip_files:
            if not os.path.isfile(zip_path):
                raise FileNotFoundError(f"Cannot merge zip files. Missing {zip_path}.")

            with zipfile.ZipFile(zip_path, "r") as zf:
                for file_name in zf.namelist():
                    # Stream copy from source ZIP into merged ZIP
                    with zf.open(file_name) as src, merged_zip.open(file_name, "w") as dst:
                        shutil.copyfileobj(src, dst)

    return Path(unsplit_zip)


def delete_unused_samples(valid_files: list[str], path_to_dir: Path) -> None:
    """
    Helper function to delete unused sound files after filtering for trigger/control/background classes.

    Params:
        valid_files (List[str]): list of file names to keep
        path_to_dir (Path): Path to the directory containing the dataset
    """

    for fname in os.listdir(path_to_dir):
        file_path = os.path.join(path_to_dir, fname)
        if os.path.isfile(file_path) and fname not in valid_files:
            os.remove(file_path)


class ESC50(SourceData):
    """
    Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
    ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """

    def __init__(self, mapping: Path, save_dir: Path) -> None:
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        esc50_dir = self.download_data(save_dir)
        self.path = os.path.join(esc50_dir, "audio")

        esc50 = self.get_metadata(esc50_dir)
        self.metadata = self.get_samples(esc50)

        self.dir_path = esc50_dir

    def download_data(self, save_dir: Path) -> Path:
        """
        Downloads and extracts the ESC50 dataset from github
        Params:
            save_dir (str): directory to save the dataset
        Returns:
            Full path to the dataset
        """
        if os.path.exists("esc50-extracted.json"):
            print(f"ESC50 dataset has already been downloaded and unzipped at {save_dir}")
            with open("esc50-extracted.json", "r") as f:
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

            with open("esc50-zip.txt", "w") as f:
                pass  # track downloading and extraction of dataset

        print("\nUnzipping ESC-50 dataset...")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        extracted_path = os.path.join(save_dir, "ESC-50-master")
        print(f"Dataset downloaded and extracted to: {extracted_path}")

        # In case another class is instantiated but dataset does not need to be redownloaded.
        if os.path.isfile("esc50-zip.txt"):
            os.rename("esc50-zip.txt", "esc50-extracted.json")
        with open("esc50-extracted.json", "w") as f:
            f.dump({"Path": extracted_path, "Meta": os.path.join(extracted_path, "meta", "esc50.csv")}, f, indent=4)

        print("Deleting ESC-50 zip file...")
        os.remove(local_zip_path)
        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Saves the downloaded metadata as a Dataframe

        """
        if os.path.exists("esc50-extracted.json"):
            with open("esc50-extracted.json", "r") as f:
                data = json.load(f)
                return Path(data["Meta"])
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
        shutil.rmtree("esc50-extracted.json")


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
            self.backgrounds = json.load(f)["Backgrounds"]

        self.path = self.download_data(save_dir)

        fsd50k = self.get_metadata(self.path)
        self.metadata = self.get_samples(fsd50k)

    def download_data(self, save_dir: Path) -> Path:
        """
        Downloads, combines, and extracts FSD50K dataset from Zenodo using multiple threads, with resume support.
        Params:
            save_dir (Path): Path to save the dataset
        Returns:
            full path of saved dataset
        """
        if os.path.exists("fsd50k-extracted.json"):
            print(f"FSD50K dataset has already been downloaded and unzipped at {save_dir}")
            with open("fsd50k-extracted.json", "r") as f:
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

        if not os.path.exists("fsd50k-zip.txt"):
            with ThreadPoolExecutor(max_workers=6) as executor:
                zip_files = list(executor.map(lambda url_hash: download_file(url_hash[0], url_hash[1], save_dir), urls))

            print(zip_files[0])

            with open("fsd50k-zip.txt", "w") as f:
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
        if os.path.isfile("fsd50k-zip.txt"):
            os.rename("fsd50k-zip.txt", "fsd50k-extracted.json")
        with open("fsd50k-extracted.json", "w") as f:
            json.dump({"Path": extracted_path}, f, indent=4)

        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Downloads FSD50K metadata from zenodo and saves as a dataframe.

        """
        # Check if metadata has already been downloaded
        if os.path.exists("fsd50k-extracted.json"):
            with open("fsd50k-extracted.json", "r") as f:
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
        with open("fsd50k-extracted.json", "r+") as f:
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

        # TODO: Find amplitude and duration of sound samples

        return fsd50k

    def delete(self) -> None:
        shutil.rmtree(self.path)
        shutil.rmtree("fsd50k-extracted.json")


class FOAMS(SourceData):
    """
    Class for FOAMS misophonia trigger sounds. Downloaded from https://zenodo.org/records/7109069
    """

    def __init__(self, save_dir: Path) -> None:
        self.path = self.download_data(save_dir)
        self.metadata = self.get_metadata(self.path)

    def download_data(self, save_dir: Path) -> Path:
        """
        Download 50 trigger samples from FOAMS at https://zenodo.org/records/7109069/files/. First checks if they have been downloaded alrady.
        Params:
            save_dir
        """
        url = "https://zenodo.org/records/7109069/files/FOAMS_processed_audio.zip?download=1"
        if not os.path.exists("foams-extracted.txt"):
            unzipped_data = download_file(url, save_dir)

            with zipfile.ZipFile(unzipped_data, "r") as zip_ref:
                zip_ref.extractall(save_dir)

            with open("foams_extracted.txt", "w") as f:
                f.write("Downloaded and extracted FOAMS dataset.")

            print("Removing FOAMS zip...")
            os.remove(unzipped_data)
        else:
            print("FOAMS dataset has already been downloaded and unzipped.")

        return Path(os.path.join(save_dir, "FOAMS_processed_audio"))

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        url = "https://zenodo.org/record/7109069/files/segmentation_info.csv?download=1"
        response = requests.get(url)
        response.raise_for_status()

        metadata_path = os.path.join(extracted_path, "segmentation_info.csv")
        with open(metadata_path, "wb") as f:
            f.write(response.content)

        metadata = pd.read_csv(metadata_path)
        metadata = metadata.rename(columns={"id": "filename", "label": "labels"})
        return metadata

    def get_samples(self) -> pd.DataFrame:
        pass

    def delete(self) -> None:
        shutil.rmtree(self.path)


class MisophoniaData:
    """
    IMPORTANT: The metadata of all SourceData objects passed to MisophoniaData should have a "filename" column and "label"
    column and "isTrig" column
    """

    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        pass

    def generate(self) -> None:
        pass

    class MisophoniaItem:
        #     component_sounds =
        #     duration
        #     amplitude
        def __init__(self) -> None:
            pass


if __name__ == "__main__":
    esc50_mapping = Path("../mappings/data/esc50_to_foams_mapping.json")

    fsd50k_mapping = Path("../data/mappings/fsd50k_to_foams_mapping.json")
    background_classes = Path("../data/mappings/background_classes.json")

    # esc50 = ESC50(mapping=esc50_mapping, save_dir=DEFAULT_DIR)
    fsd50k = FSD50K(mapping=fsd50k_mapping, backgrounds=background_classes, save_dir=DEFAULT_DIR)
    # foams = FOAMS(save_dir=DEFAULT_DIR)
