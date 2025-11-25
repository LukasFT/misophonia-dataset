from pathlib import Path

import pandas as pd

from ..interface import SourceData, SourceMetaData, get_default_data_dir
from ._downloading import download_and_unzip, download_single_file, is_downloaded, is_unzipped


class FoamsDataset(SourceData):
    """
    Class for FOAMS misophonia trigger sounds. Downloaded from https://zenodo.org/records/7109069
    """

    def __init__(self, save_dir: Path | None = None) -> None:
        self._base_save_dir = save_dir if save_dir is not None else get_default_data_dir(dataset_name="FOAMS")

    def is_downloaded(self) -> bool:
        return is_unzipped(file_path=self._base_save_dir / "FOAMS_processed_audio.zip") and is_downloaded(
            file_path=self._base_save_dir / "segmentation_info.csv"
        )

    def download_data(self) -> None:
        """
        Download 50 trigger samples from FOAMS at https://zenodo.org/records/7109069/files/. First checks if they have been downloaded alrady.
        Params:
            save_dir
        """
        download_and_unzip(
            files=(
                {
                    # Latest commit per November 24, 2025
                    "url": "https://zenodo.org/records/8170225/files/FOAMS_processed_audio.zip?download=1",
                    "md5": "89e717006cea3687384baa3c86d6307c",
                },
            ),
            save_dir=self._base_save_dir,
            delete_zip=True,
            rename_extracted_dir="processed_audio",
        )
        download_single_file(
            url="https://zenodo.org/records/8170225/files/segmentation_info.csv?download=1",
            md5="0ac1de8a66ffb52be34722ad8cd5e514",
            save_dir=self._base_save_dir,
        )

    def get_metadata(self) -> SourceMetaData:
        meta = pd.read_csv(self._base_save_dir / "segmentation_info.csv")
        meta = meta.add_prefix("foams_")  # to avoid confusion with other datasets

        meta["source_dataset"] = "FOAMS"

        meta = meta.rename(
            columns={
                "foams_id": "freesound_id",  # FOAMS IDs correspond to FreeSound IDs
                "foams_label": "labels",  # FOAMS labels are already aligned to FOAMS taxonomy
            }
        )

        meta["labels"] = meta["labels"].apply(lambda x: [x])  # Make singular lists to align with other datasets
        meta["label_type"] = "trigger"  # All FOAMS sounds are triggers
        meta["file_path"] = meta["freesound_id"].apply(
            lambda x: str(self._base_save_dir / "processed_audio" / f"{x}_processed.wav")
        )

        def _get_dataset_license() -> tuple[dict, ...]:
            return (
                # Source sound license:
                {  # TODO: Find license for the sounds themselves
                    "license_url": "N/A",
                    "attribution_name": "N/A",
                    "attribution_url": "N/A",
                },
                # Dataset license:
                {
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "attribution_name": "D. M. Orloff, D. Benesch & H. A. Hansen",
                    "attribution_url": "https://doi.org/10.5334/jopd.94",
                },
            )

        meta["licensing"] = meta["freesound_id"].apply(lambda _: _get_dataset_license())

        return SourceMetaData.validate(meta)

    def delete(self) -> None:
        self._base_save_dir.rmdir()
