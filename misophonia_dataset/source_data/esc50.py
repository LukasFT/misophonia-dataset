import json
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

    def get_metadata(self) -> SourceMetaData:
        """
        Get standardized metadata for ESC50 dataset.
        """
        assert self.is_downloaded(), "Dataset is not downloaded yet."
        meta = pd.read_csv(self._base_unzipped_dir / "meta" / "esc50.csv")
        meta = meta.add_prefix("esc50_")  # to avoid confusion with other datasets

        meta["source_dataset"] = "ESC50"

        base_audio_dir = (self._base_unzipped_dir / "audio").expanduser().resolve()
        meta["file_path"] = meta["esc50_filename"].apply(lambda x: str(base_audio_dir / x))

        meta["labels"] = meta["esc50_category"].apply(lambda x: self.mapping.get(str(x), {}).get("foams_mapping", None))

        meta = meta[meta["label"].notna()]  # Only use trigger sounds from ESC50
        meta["sound_type"] = "trigger"

        meta = meta.rename(columns={"esc50_src_file": "freesound_id"})

        def get_dataset_license(*, is_esc10: bool) -> str:
            return (
                # Source sound license:
                {  # TODO: Find license for the sounds themselves
                    "license_url": "N/A",
                    "attribution_name": "N/A",
                    "attribution_url": "N/A",
                },
                # Dataset license:
                {
                    "license_url": (  # See their README.md
                        "https://creativecommons.org/licenses/by/3.0/"
                        if is_esc10
                        else "https://creativecommons.org/licenses/by-nc/3.0/"
                    ),
                    "attribution_name": "K. J. Piczak",
                    "attribution_url": "http://dx.doi.org/10.1145/2733373.2806390",
                },
            )

        meta["licensing"] = meta["esc50_esc10"].apply(lambda x: get_dataset_license(is_esc10=x))

        return SourceMetaData.validate(meta)

    def delete(self) -> None:
        self._base_save_dir.rmdir()
