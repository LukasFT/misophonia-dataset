"""This is a script to transform the freesound information from https://github.com/LAION-AI/audio-dataset/tree/main/laion-audio-630k into our format and save it"""

import json
from collections.abc import Collection
from pathlib import Path

import pandas as pd

from ..interface import LicenseT

LICENSE_JSON_PATH = Path(__file__).parent / "freesound_license.json"


def get_freesound_licenses() -> dict[str, LicenseT]:
    with LICENSE_JSON_PATH.open("r") as f:
        return json.load(f)


def generate_freesound_licenses(
    freesound_ids: pd.Series,
    base_licenses: Collection[LicenseT] = (),
    fallback: LicenseT = {"license_url": "N/A", "attribution_name": "Unknown Author", "attribution_url": ""},
) -> pd.Series:
    freesound_licenses = get_freesound_licenses()

    def _get_dataset_license(freesound_id: str) -> tuple[dict, ...]:
        return (
            freesound_licenses.get(freesound_id, fallback),
            *base_licenses,
        )

    return freesound_ids.astype(str).apply(lambda freesound_id: _get_dataset_license(freesound_id))


def _generate_license_dict(row) -> LicenseT:  # noqa: ANN001
    return {
        "license_url": row["license"],
        "attribution_name": row["username"],
        "attribution_url": f"https://freesound.org/people/{row['username']}/",
    }


if __name__ == "__main__":
    license_in_path = Path("data/freesound_license_all.csv")

    print("This script is used to generate a pre-made licese file")
    print("Download https://drive.google.com/file/d/1xF3K5x0RAhBNGKSMvE13cuvrIZLs6M3K/view?usp=share_link manually")
    print(f"Place it in {license_in_path}")
    assert license_in_path.exists(), f"{license_in_path} does not exist"

    all_license = pd.read_csv(license_in_path)
    print(f"Loaded {len(all_license)} license entries")

    license_dict = {row["id"]: _generate_license_dict(row) for _, row in all_license.iterrows()}
    with LICENSE_JSON_PATH.open("w") as f:
        json.dump(license_dict, f)

    print(f"Saved license file to {LICENSE_JSON_PATH}")
