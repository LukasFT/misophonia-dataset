import json
import os
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from interface import SourceData, DEFAULT_DIR
from tqdm import tqdm
from time import time


def download_file(url: str, save_dir: Path) -> Path:
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

    # Should never reach here
    return Path(save_path)


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
        url = "https://github.com/karoldvl/ESC-50/archive/master.zip"

        os.makedirs(save_dir, exist_ok=True)
        local_zip_path = os.path.join(save_dir, "ESC-50.zip")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024 * 1024

        # Stream download to show progress
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

        print("Unzipping ESC-50 dataset...")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        extracted_path = os.path.join(save_dir, "ESC-50-master")
        print(f"Dataset downloaded and extracted to: {extracted_path}")

        print("Deleting ESC-50 zip file...")
        os.remove(local_zip_path)
        return extracted_path

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Saves the downloaded metadata as a Dataframe

        """
        print("Saving metadata...")
        metadata_path = os.path.join(extracted_path, "meta", "esc50.csv")
        metadata = pd.read_csv(metadata_path)
        return metadata

    def get_samples(self, esc50: pd.DataFrame) -> pd.DataFrame:
        # Only keeping metadata for triggers
        trigger_classes = [k for k in self.mapping.keys()]
        esc50_triggers = esc50[esc50["category"].isin(trigger_classes)]

        print("Filtering trigger samples from ESC50...")
        esc50_triggers.loc[:, "category"] = esc50_triggers["category"].apply(
            lambda x: self.mapping[str(x)]["foams_mapping"]
        )
        esc50_triggers.rename(columns={"category": "labels"}, inplace=True)
        esc50_triggers.loc[:, "isTrig"] = 1

        # TODO: Add duration and amplitude to the metadata

        return esc50_triggers

    def delete(self) -> None:
        shutil.rmtree(self.dir_path)


class FSD50K(SourceData):
    """
    Class for the FSD50K dev set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
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
        urls = [
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.zip?download=1",
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z01?download=1",
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z02?download=1",
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z03?download=1",
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z04?download=1",
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z05?download=1",
        ]

        os.makedirs(save_dir, exist_ok=True)

        # with ThreadPoolExecutor(max_workers=3) as executor:
        #     zip_files = list(executor.map(lambda url: download_file(url, save_dir), urls))

        zip_files = [
            "../data/FSD50K.dev_audio.z01",
            "../data/FSD50K.dev_audio.z02",
            "../data/FSD50K.dev_audio.z03",
            "../data/FSD50K.dev_audio.z04",
            "../data/FSD50K.dev_audio.z05",
            "../data/FSD50K.dev_audio.zip",
        ]

        # subprocess.run(["zip", "-s", "0", split_zip, "--out", unsplit_zip], check=True)

        fragments = list(Path("../data").glob("FSD50K.dev_audio.*"))

        # sort: main .zip first, then the rest
        fragments = sorted(fragments, key=lambda p: (p.suffix != ".zip", p.suffix))
        print(fragments)
        unsplit_zip = Path("../data/unsplit.zip")
        with open(unsplit_zip, "wb") as outfile:
            for frag in fragments:
                with open(frag, "rb") as infile:
                    shutil.copyfileobj(infile, outfile, length=16 * 1024 * 1024)

        # First remove component zip files
        # for file in zip_files:
        #     os.remove(file)

        print("Unzipping FSD50K dataset...")
        with zipfile.ZipFile(unsplit_zip, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        # Deleting zip files
        print("Deleting FSD50K zip file...")
        zip_files.append(unsplit_zip)

        extracted_path = os.path.join(save_dir, "FSD50K.dev_audio")
        return Path(extracted_path)

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
        Downloads FSD50K metadata from zenodo and saves as a dataframe.

        """
        # Download metadata folder
        url = "https://zenodo.org/records/4060432/files/FSD50K.metadata.zip?download=1"
        unzipped_meta = download_file(url, extracted_path)

        # Extract all to FSD50K.dev_audio folder
        with zipfile.ZipFile(unzipped_meta, "r") as zip_ref:
            zip_ref.extractall(extracted_path)

        # Remove zip file
        os.remove(unzipped_meta)

        metadata_path = os.path.join(extracted_path, "FSD50K.metadata", "collection", "collection_dev.csv")

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
        fsd50k = fsd50k[fsd50k["category"] >= 0].copy()

        # Update label mapping only for Trigger rows
        fsd50k.loc[fsd50k["isTrig"] == 1, "labels"] = fsd50k.loc[fsd50k["isTrig"] == 1, "labels"].apply(
            lambda x: self.mapping["Trigger"][str(x)]["foams_mapping"]
        )

        # Fix rename syntax
        fsd50k.rename(columns={"fname": "filename"}, inplace=True)

        # TODO: Find amplitude and duration of sound samples

        return fsd50k

    def delete(self) -> None:
        shutil.rmtree(self.path)


class FOAMS(SourceData):
    """
    Class for FOAMS misophonia trigger sounds. Downloaded from https://zenodo.org/records/7109069
    """

    def __init__(self, save_dir: Path) -> None:
        self.path = self.download_data(save_dir)
        self.metadata = self.get_metadata(self.path)

    def download_data(self, save_dir: Path) -> Path:
        """
        Download 50 trigger samples from FOAMS at https://zenodo.org/records/7109069/files/.
        Params:
            save_dir
        """
        url = "https://zenodo.org/records/7109069/files/FOAMS_processed_audio.zip?download=1"

        unzipped_data = download_file(url, save_dir)

        with zipfile.ZipFile(unzipped_data, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        print("Removing FOAMS zip...")
        os.remove(unzipped_data)

        return Path(os.path.join(save_dir, "FOAMS_processed_audio"))

    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        url = "https://zenodo.org/record/7109069/files/segmentation_info.csv?download=1"
        response = requests.get(url)
        response.raise_for_status()

        metadata_path = os.path.join(extracted_path, "segmentation_info.csv")
        with open(metadata_path, "wb") as f:
            f.write(response.content)

        metadata = pd.read_csv(metadata_path)
        metadata.rename(columns={"id": "filename", "label": "labels"}, inplace=True)
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
    esc50_mapping = Path("../data/esc50_to_foams_mapping.json")

    fsd50k_mapping = Path("../data/fsd50k_to_foams_mapping.json")
    background_classes = Path("../data/background_classes.json")

    # esc50 = ESC50(mapping=esc50_mapping, save_dir=DEFAULT_DIR)
    fsd50k = FSD50K(mapping=fsd50k_mapping, backgrounds=background_classes, save_dir=DEFAULT_DIR)
    # foams = FOAMS(save_dir=DEFAULT_DIR)
