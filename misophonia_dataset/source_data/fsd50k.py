import json
from pathlib import Path

import pandas as pd

from ..interface import MappingT, SourceData, SourceMetaData, get_default_data_dir
from ._downloading import download_and_unzip, is_unzipped


class Fsd50kDataset(SourceData):
    """
    Class for the FSD50K dev set. Data is downloaded from Zenodo, https://zenodo.org/records/4060432.
    When downloading and unzipping the dataset, txt files are generated to track progress.
    Controls, triggers, and backgrounds are sampled from FSD50K.
    """

    def __init__(
        self,
        *,
        trigger_mapping: None | MappingT = None,
        control_mapping: None | MappingT = None,
        backgrounds: list[str] | None = None,
        save_dir: Path | None = None,
    ) -> None:
        if trigger_mapping is None:
            with (Path(__file__).parent / "fsd50k_mapping.json").open("r") as f:
                trigger_mapping = json.load(f)["Trigger"]
        self.trigger_mapping: MappingT = trigger_mapping

        if control_mapping is None:
            with (Path(__file__).parent / "fsd50k_mapping.json").open("r") as f:
                control_mapping = json.load(f)["Control"]
        self.control_mapping: MappingT = control_mapping

        if backgrounds is None:
            with (Path(__file__).parent / "fsd50k_background_classes.json").open("r") as f:
                backgrounds = json.load(f)
        self.backgrounds: list[str] = backgrounds

        self._base_save_dir = Path(save_dir) if save_dir is not None else get_default_data_dir(dataset_name="FSD50K")

    def is_downloaded(self) -> bool:
        return all(
            is_unzipped(file_path=self._base_save_dir / part)
            for part in ("FSD50K.metadata.zip", "FSD50K.dev_audio.zip", "FSD50K.eval_audio.zip")
        )

    def download_data(self) -> None:
        """
        Downloads, combines, and extracts FSD50K dataset from Zenodo using multiple threads, with resume support.

        Params:
            save_dir (Path): Path to save the dataset

        Returns:
            full path of saved dataset
        """

        data_specs = {
            "metadata": (
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.metadata.zip?download=1",
                    "md5": "b9ea0c829a411c1d42adb9da539ed237",
                },
            ),
            "eval_audio": (
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.eval_audio.zip?download=1",
                    "md5": "6fa47636c3a3ad5c7dfeba99f2637982",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.eval_audio.z01?download=1",
                    "md5": "3090670eaeecc013ca1ff84fe4442aeb",
                },
            ),
            "dev_audio": (
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.zip?download=1",
                    "md5": "c480d119b8f7a7e32fdb58f3ea4d6c5a",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z01?download=1",
                    "md5": "faa7cf4cc076fc34a44a479a5ed862a3",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z02?download=1",
                    "md5": "8f9b66153e68571164fb1315d00bc7bc",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z03?download=1",
                    "md5": "1196ef47d267a993d30fa98af54b7159",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z04?download=1",
                    "md5": "d088ac4e11ba53daf9f7574c11cccac9",
                },
                {
                    "url": "https://zenodo.org/records/4060432/files/FSD50K.dev_audio.z05?download=1",
                    "md5": "81356521aa159accd3c35de22da28c7f",
                },
            ),
        }

        for spec_name, spec in data_specs.items():
            download_and_unzip(
                files=spec,
                save_dir=self._base_save_dir,
                rename_extracted_dir=spec_name,
                delete_zip=True,
            )

    def get_metadata(self) -> SourceMetaData:
        """
        Collects triggers, controls, backgrounds from full FSD50K.dev set using predefined class mappings.
        Removes all unused sound samples.
        Params:
            fsd50k (dataframe): full metadata for dataset
        Returns:
            new metadata dataframe including only the collected sound samples.
        """
        assert self.is_downloaded(), "Dataset is not downloaded yet."

        # Load and combine dev + eval metadata
        meta_dev = pd.read_csv(self._base_save_dir / "metadata" / "collection" / "collection_dev.csv")
        meta_dev["split"] = "dev"
        meta_eval = pd.read_csv(self._base_save_dir / "metadata" / "collection" / "collection_eval.csv")
        meta_eval["split"] = "eval"
        meta = pd.concat([meta_dev, meta_eval], ignore_index=True)
        meta = meta.add_prefix("fsd50k_")  # Prefix original columns to avoid conflicts

        meta["source_dataset"] = "FSD50K"

        meta["freesound_id"] = meta["fsd50k_fname"]  # The filename base is just the freesound id

        meta["file_path"] = meta.apply(
            lambda row: str(self._base_save_dir / f"{row['fsd50k_split']}_audio" / f"{row['fsd50k_fname']}.wav"), axis=1
        )

        meta["fsd50k_labels"] = meta["fsd50k_labels"].astype(str).str.split(",")

        def _apply_foams_mapping(series: pd.Series, mapping: MappingT) -> pd.Series:
            return series.apply(
                lambda labels: [mapping.get(label, {}).get("foams_mapping") for label in labels if label in mapping]
            )

        # Only keep rows with one or more of the collected labels, but they should all be of the same type and no other labels
        trigger_labels = _apply_foams_mapping(meta["fsd50k_labels"], self.trigger_mapping)
        control_labels = _apply_foams_mapping(meta["fsd50k_labels"], self.control_mapping)
        background_labels = meta["fsd50k_labels"].apply(
            lambda labels: [label for label in labels if label in self.backgrounds]
        )
        trigger_labels_len = trigger_labels.map(len)
        control_labels_len = control_labels.map(len)
        background_labels_len = background_labels.map(len)
        total_labels_len = meta["fsd50k_labels"].map(len)
        meta = meta[
            # Has labels of exactly one type:
            (
                (
                    (trigger_labels_len > 0).astype(int)
                    + (control_labels_len > 0).astype(int)
                    + (background_labels_len > 0).astype(int)
                )
                == 1
            )
            &  # And no other labels:
            ((trigger_labels_len + control_labels_len + background_labels_len) == total_labels_len)
        ]

        # Assign label_type and labels based on which label set is non-empty
        def _determine_label_type_and_labels(row: pd.Series) -> tuple[str, list[str]]:
            if len(trigger_labels[row.name]) > 0:
                return "trigger", list(set(trigger_labels[row.name]))
            elif len(control_labels[row.name]) > 0:
                return "control", list(set(control_labels[row.name]))
            else:
                return "background", list(set(background_labels[row.name]))

        meta[["label_type", "labels"]] = meta.apply(_determine_label_type_and_labels, axis=1, result_type="expand")

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
                    "attribution_name": "E. Fonseca, X. Favory, J. Pons, F. Font & X. Serra",
                    "attribution_url": "https://ieeexplore.ieee.org/document/9645159",
                },
            )

        meta["licensing"] = meta["freesound_id"].apply(lambda _: _get_dataset_license())

        return SourceMetaData.validate(meta)

    def delete(self) -> None:
        self._base_save_dir.rmdir()

    def __str__(self) -> str:
        return "FSDK50 Dataset"
