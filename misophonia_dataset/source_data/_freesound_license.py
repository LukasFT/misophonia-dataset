"""This is a script to transform the freesound information from https://github.com/LAION-AI/audio-dataset/tree/main/laion-audio-630k into our format and save it"""

import os
from collections.abc import Collection
from pathlib import Path

import pandas as pd
import requests

from ..interface import LicenseT

LICENSE_STORE_PATH = Path(__file__).parent / "freesound_license.csv"


def get_freesound_licenses() -> pd.DataFrame:
    return pd.read_csv(LICENSE_STORE_PATH, index_col="freesound_id")


def generate_freesound_licenses(
    freesound_ids: pd.Series,
    base_licenses: Collection[LicenseT] = (),
    fallback: LicenseT = {"license_url": "N/A", "attribution_name": "Unknown Author", "attribution_url": ""},
) -> pd.Series:
    freesound_licenses = get_freesound_licenses()

    def _get_dataset_license(freesound_id: str) -> tuple[dict, ...]:
        license = freesound_licenses.get(freesound_id)

        if license is None:
            license = _get_from_freesound_api(freesound_id)
            freesound_licenses.loc[freesound_id] = license  # Cache for future use

        if license is None:
            license = fallback

        return (
            freesound_licenses.get(freesound_id, fallback),
            *base_licenses,
        )

    result = freesound_ids.astype(str).apply(lambda freesound_id: _get_dataset_license(freesound_id))

    # save updated licenses
    freesound_licenses.to_csv(LICENSE_STORE_PATH)

    return result


def _get_from_freesound_api(freesound_id: str) -> LicenseT:
    api_token = os.getenv("FREESOUND_API_TOKEN")
    assert api_token is not None, (
        "FREESOUND_API_TOKEN environment variable not set. It is needed to get freesound licenses."
    )

    url = f"https://freesound.org/apiv2/sounds/{freesound_id}/?fields=license,username,url&token={api_token}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return _generate_info(freesound_id, data["license"], data["username"])


def _generate_info(freesound_id: str, license_url: str, username: str) -> LicenseT:  # noqa: ANN001
    return {
        "license_url": license_url,
        "attribution_name": username,
        "attribution_url": f"https://freesound.org/people/{username}/sounds/{freesound_id}/",
    }


def _generate_from_row(row) -> LicenseT:  # noqa: ANN001
    # if row["license"] is not a valid URL, return None (it happened in some cases ...)
    import re

    def _is_valid_url(url: str) -> bool:
        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
            r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return re.match(regex, url) is not None

    if not _is_valid_url(row["license"]):
        return None
    return _generate_info(row["id"], row["license"], row["username"])


def get_base_licensing_from_clap() -> None:
    """
    Generate a base license file from the CLAP data.

    This was the largest available collection of FreeSound license information we could find, in order to limit API calls to FreeSound.

    """
    if LICENSE_STORE_PATH.exists():
        print(f"License file {LICENSE_STORE_PATH} already exists, skipping generation.")
        return

    license_in_path = Path("data/freesound_license_all.csv")

    print("This script is used to generate a pre-made licese file")
    print("Download https://drive.google.com/file/d/1xF3K5x0RAhBNGKSMvE13cuvrIZLs6M3K/view?usp=share_link manually")
    print(f"Place it in {license_in_path}")
    assert license_in_path.exists(), f"{license_in_path} does not exist"

    all_license = pd.read_csv(license_in_path)
    print(f"Loaded {len(all_license)} license entries")

    license_dicts = all_license.copy()
    license_dicts["licensing"] = all_license.apply(_generate_from_row, axis=1)
    license_dicts = license_dicts[["id", "licensing"]].rename(columns={"id": "freesound_id"})
    license_dicts = license_dicts.set_index("freesound_id")

    license_dicts = license_dicts[license_dicts["licensing"].notna()]

    license_dicts = license_dicts[~license_dicts.index.duplicated(keep="first")]

    license_dicts.to_csv(LICENSE_STORE_PATH)

    print(f"Saved license file to {LICENSE_STORE_PATH}")


if __name__ == "__main__":
    get_base_licensing_from_clap()
