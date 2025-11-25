"""This is a script to transform the freesound information from https://github.com/LAION-AI/audio-dataset/tree/main/laion-audio-630k into our format and save it"""

import json
import os
import time
from collections.abc import Collection
from pathlib import Path

import pandas as pd
import requests

from ..interface import LicenseT

LICENSE_STORE_PATH = Path(__file__).parent / "freesound_license.csv"


def get_freesound_licenses() -> pd.DataFrame:
    freesound_licenses = pd.read_csv(LICENSE_STORE_PATH, index_col="freesound_id")
    freesound_licenses["licensing"] = freesound_licenses["licensing"].apply(json.loads)
    return freesound_licenses


def generate_freesound_licenses(
    freesound_ids: pd.Series,
    base_licenses: Collection[LicenseT] = (),
    retries: int = 10,
) -> pd.Series:
    try:
        return _generate_freesound_licenses(
            freesound_ids=freesound_ids,
            base_licenses=base_licenses,
        )
    except requests.exceptions.RequestException as e:
        if retries > 0:
            backoff_time = 2 ** (10 - retries)
            print(f"RequestException occurred: {e}. Retrying {retries} more times after {backoff_time} seconds...")
            time.sleep(backoff_time)
            return generate_freesound_licenses(
                freesound_ids=freesound_ids,
                base_licenses=base_licenses,
                retries=retries - 1,
            )
        else:
            raise RuntimeError("Maximum retries reached for FreeSound API requests.") from e


def _generate_freesound_licenses(
    freesound_ids: pd.Series,
    base_licenses: Collection[LicenseT] = (),
) -> pd.Series:
    freesound_licenses = get_freesound_licenses()
    updates = {}

    def _get_dataset_license(freesound_id: int) -> tuple[dict, ...]:
        lic = freesound_licenses["licensing"].loc[freesound_id] if freesound_id in freesound_licenses.index else None

        if lic is None:
            lic = _get_from_freesound_api(freesound_id)
            updates[freesound_id] = {"licensing": lic}

        return (
            lic,
            *base_licenses,
        )

    try:
        return freesound_ids.astype(int).apply(lambda freesound_id: _get_dataset_license(freesound_id))
    finally:
        # save updated licenses (also if an error occurred)
        if len(updates) > 0:
            new_licenses = pd.DataFrame.from_dict(updates, orient="index")
            new_licenses.index.name = "freesound_id"
            all_licenses = pd.concat([freesound_licenses, new_licenses])
            all_licenses["licensing"] = all_licenses["licensing"].apply(json.dumps)
            all_licenses.to_csv(LICENSE_STORE_PATH)


def _get_from_freesound_api(freesound_id: str) -> LicenseT:
    api_token = os.getenv("FREESOUND_API_TOKEN")
    assert api_token is not None, (
        "FREESOUND_API_TOKEN environment variable not set. It is needed to get freesound licenses."
    )

    url = f"https://freesound.org/apiv2/sounds/{freesound_id}/?fields=license,username,url&token={api_token}"
    response = requests.get(url)

    if response.status_code == 404:
        return {
            "license_url": "N/A",
            "attribution_name": "N/A",
            "attribution_url": "N/A",
        }

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

    license_dicts["licensing"] = license_dicts["licensing"].apply(json.dumps)

    license_dicts.to_csv(LICENSE_STORE_PATH)

    print(f"Saved license file to {LICENSE_STORE_PATH}")


if __name__ == "__main__":
    get_base_licensing_from_clap()
