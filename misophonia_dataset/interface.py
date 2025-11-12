from abc import ABC
from enum import Enum
from pathlib import Path
import os
import requests
import zipfile
from tqdm import tqdm
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import json
import shutil


def download_file(url: str, save_dir: Path):
    """
        Helper function to download large files from the web. Displays progress bar and provides resume support.
        Used primarily for FSD50K and FSD50K_eval datasets.

        Params:
            url (str): url from which to download the file
            save_dir (Path): path to save the file
        Returns:
            the full path of the saved file
    """

    # Extract filename and remove query parameters
    filename = os.path.basename(urlparse(url).path)
    save_path = os.path.join(save_dir, filename)

    # Stream download
    headers = {}
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers = {"Range": f"bytes={existing_size}-"}
    else:
        existing_size = 0

    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0)) + existing_size
    chunk_size = 1024 * 1024  # 1 MB

    mode = "ab" if existing_size else "wb"

    with open(save_path, mode) as f, tqdm(
        total=total_size,
        initial=existing_size,
        unit='B',
        unit_scale=True,
        desc=f"Downloading {filename}",
        ascii=True
    ) as bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))

    return save_path


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
        # columns: 
        # id, license_url, licence_aatribution, ..., 
        # misophnia_labels
        # audioset_labels
        # split
        # audio_path
        pass

    @abstractmethod
    def get_samples(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def delete(self) -> None


class ESC50(SourceData):
    """
        Class for the ESC50 dataset. Data is downloaded from "https://github.com/karoldvl/ESC-50/archive/master.zip".
        ESC50 is only used for trigger sounds, so the isTrig of the metadata column will have only 1s.
    """
    def __init__(
            self,
            mapping: Path,
            save_dir: Path
        ):
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        self.path = self.download_data(save_dir)

        esc50 = self.get_metadata(self.path)
        self.metadata = self.get_triggers(esc50)



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

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024

        # Stream download to show progress
        with open(local_zip_path, "wb") as file, tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            desc="Downloading",
            ascii=True,
        ) as bar:
            for data in response.iter_content(block_size):
                file.write(data)
                bar.update(len(data))

        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        os.remove(local_zip_path)

        extracted_path = os.path.join(save_dir, "ESC-50-master")
        print(f"Dataset downloaded and extracted to: {extracted_path}")

        return os.path.join(extracted_path, "audio")


    def get_metadata(self, extracted_path: Path) -> pd.DataFrame:
        """
            Saves the downloaded metadata as a Dataframe

        """
        metadata_path = os.path.join(extracted_path, "meta", "esc50.csv")
        metadata = pd.read_csv(metadata_path)


    def get_samples(self, esc50: pd.DataFrame) -> pd.DataFrame:

        # Only keeping metadata for triggers
        trigger_classes = [k for k in self.mapping.keys()]
        esc50_triggers = esc50[esc50["category"].isin(trigger_classes)]

        esc50_triggers.loc[:, "category"] = esc50_triggers["category"].apply(lambda x: mapping[str(x)]["foams_mapping"])
        esc50_triggers.rename(columns={"category": "labels"}, inplace=True)
        esc50_triggers["isTrig"] = 1

        # Deleting all files that should not be kept
        valid_files = set(esc50_triggers['filename'])

        for fname in os.listdir(self.path):
            file_path = os.path.join(self.path, fname)
            if os.path.isfile(file_path) and fname not in valid_files:
                os.remove(file_path)

        return esc50_triggers


    def delete(self):
        shutil.rmtree(self.path)


class FSDK50(SourceData):
    """
        Class for the FSD50K dev set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
        Controls, triggers, and backgrounds are sampled from FSD50K.
    """
    def __init__(self,
               mapping: Path,
               backgrounds: Path,
               save_dir: Path
    ):
        with open(mapping, "r") as f:
            self.mapping = json.load(f)

        with open(backgrounds, "r") as f:
            self.backgrounds = json.load(f)["Backgrounds"]

        self.path = self.download_data(save_dir)

        fsd50k = self.get_metadata(self.path)
        self.metadata = self.get_triggers(fsd50k)


    def download_data(self, save_dir: Path):
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
            "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z05?download=1"
        ]

        os.makedirs(save_dir, exist_ok=True)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            zip_files = list(executor.map(lambda url: download_file(url, save_dir), urls))

        # Combining zip files and unzipping
        split_zip = os.path.join(save_dir, "FSD50K.dev_audio.zip")
        unsplit_zip = os.path.join(save_dir + "unsplit.zip")
        subprocess.run(["zip", "-s", "0", split_zip, "--out", unsplit_zip], check=True)

        os.makedirs(os.path.j)
        with zipfile.ZipFile(unsplit_zip, "r") as zip_ref:
            zip_ref.extractall(save_dir)

        # Deleting zip files
        results.append(unsplit_zip)
        for file in zip_files:
            os.remove(file)

        extracted_path = os.path.join(save_dir, "FSD50K.dev_audio")
        return extracted_path


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
            fsd_50k["labels"].isin(control_classes),
            fsd_50k["labels"].isin(trigger_classes),
            fsd_50k["labels"].isin(self.backgrounds)
        ]
        choices = [0, 1, 2]


        # Only keep rows of collected samples
        fsd_50k["isTrig"] = np.select(conditions, choices, default=-1)
        fsd_50k = fsd_50k[fsd_50k["category"] >= 0]
        fsd_50k.loc[fsd_50k["isTrig"] == 1, "labels"] = fsd_50k.loc[fsd_50k["isTrig"] == 1, "labels"].apply(
            lambda x: mapping["Trigger"][str(x)]["foams_mapping"]
        )

        fsd50k.rename(column=["fname": "filename"], inplace=True)

        return fsd50k

    def delete(self):
        shutil.rmtree(self.path)

class FOAMS(SourceData):
    def __init__(self,
               metadata: str,
               label_column_name: Path, #label column name in metadata
               fname_column_name: Path, # fname column name in metadata
            ):
        pass    
        


class MisophoniaData:
    """
        IMPORTANT: The metadata of all SourceData objects passed to MisophoniaData should have a "filename" column and "label"
        column and "isTrig" column
    """
    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        pass

    def generate(self):
        pass

class MisophoniaItem:
    component_sounds =
    duration
    amplitude

    pass

def generate_misophonia_data(source_data: list[SourceData], split: Split) -> Generator[MisophoniaItem]:
    combined_metadata = pd.DataFrame

    while True:
        yield MisophoniaItem()

