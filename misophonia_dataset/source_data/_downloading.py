import hashlib
import json
import os
import shutil
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import eliot
import requests
from tqdm import tqdm


def is_downloaded(file_path: Path, state_file: Path | None = None) -> bool:
    """
    Checks if a file has been downloaded based on the state file.
    """
    state_file = state_file or _get_default_state_file(file_path)
    return _get_file_state(state_file).get("downloaded", False)


def is_unzipped(file_path: Path, state_file: Path | None = None) -> bool:
    """
    Checks if a file has been unzipped based on the state file.
    """
    state_file = state_file or _get_default_state_file(file_path)
    return _get_file_state(state_file).get("unzipped", False)


def download_file(
    *,
    url: str,
    save_dir: Path,
    md5: str,
    filename: str | None = None,
    unzip: bool = False,
    delete_zip: bool = False,
    rename_extracted_dir: str | None = None,
    state_file: Path | None = None,
    max_retries: int = 5,
) -> Path:
    """
    Helper function to download large files from the web. Displays progress bar and provides resume support.
    Used primarily for FSD50K and FSD50K_eval datasets.

    Params:
        url (str): url from which to download the file
        save_dir (Path): path to save the file
        md5 (str): expected md5 checksum of the file
        filename (str | None): optional name to save the file as (if None, uses name from URL)
        unzip (bool): whether to unzip the file after downloading
        delete_zip (bool): whether to delete the zip file after unzipping
        rename_extracted_dir (str | None): optional new name for the extracted directory
        state_file (Path | None): optional path to a JSON file to track download/unzip state
        max_retries (int): number of times to retry download on failure
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
    assert not (delete_zip and not unzip), "Cannot delete zip if not unzipping."

    # Remove query params
    filename = os.path.basename(urlparse(url).path) if filename is None else filename
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    state_file = state_file or _get_default_state_file(save_path)

    if not _get_file_state(state_file).get("downloaded", False):
        for attempt in range(1, max_retries + 1):
            _set_file_state(state_file, downloaded=False)
            try:
                _download_single(url, save_path)
                break  # Successful download, exit retry loop
            except Exception as e:
                if attempt == max_retries:
                    raise RuntimeError(f"Failed to download {filename} after {max_retries} attempts.") from e

                sleep_time = 1.5**attempt
                eliot.log_message(
                    f"Error downloading {filename} (attempt {attempt}/{max_retries}; retrying in {sleep_time:.1f} seconds): {e}",
                    level="warning",
                )
                time.sleep(sleep_time)

        # Check integrity of files
        if md5 is not None and not _is_correct_md5(save_path, md5):
            raise ValueError(f"MD5 checksum does not match for downloaded file: {save_path} (expected: `{md5}`)")

        _set_file_state(state_file, downloaded=True)

    if unzip:
        _unzip_file(
            save_path, save_dir, state_file=state_file, delete_zip=delete_zip, rename_extracted_dir=rename_extracted_dir
        )

    return save_path


def _get_default_state_file(save_path: Path) -> Path:
    return save_path.parent / f"state_{save_path.name}.json"


def _is_correct_md5(file: Path, md5: str) -> bool:
    with file.open("rb") as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(8192):
            md5_hash.update(chunk)
        md5_hash = md5_hash.hexdigest()

    return md5_hash == md5


def _unzip_file(
    zip_path: Path,
    extract_to: Path,
    state_file: Path | None = None,
    *,
    delete_zip: bool = False,
    rename_extracted_dir: str | None = None,
) -> None:
    state_file = state_file or (extract_to / f"state_unzip_{zip_path.name}.json")

    if _get_file_state(state_file).get("unzipped", False):
        eliot.log_message(f"File {zip_path} has already been unzipped to {extract_to}", level="info")
        return

    eliot.log_message(f"Unzipping file {zip_path} to {extract_to}", level="debug")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

        if rename_extracted_dir:
            # Check if there is exactly one top-level directory
            top_level_items = {Path(p).parts[0] for p in zip_ref.namelist()}
            # Filter out __MACOSX if present, as it's a common artifact
            top_level_items.discard("__MACOSX")

            if len(top_level_items) == 1:
                original_name = list(top_level_items)[0]
                original_path = extract_to / original_name
                new_path = extract_to / rename_extracted_dir

                if original_path.is_dir():
                    if new_path.exists():
                        shutil.rmtree(new_path)
                    original_path.rename(new_path)
                    eliot.log_message(f"Renamed {original_path.name} to {new_path.name}", level="debug")
            else:
                eliot.log_message(
                    f"Skipping rename: Zip file does not have a single top-level directory (found {top_level_items})",
                    level="warning",
                )

    if delete_zip:
        zip_path.unlink()  # Delete zip file after unzipping

    _set_file_state(state_file, unzipped=True)


def _get_file_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {}
    with state_file.open("r") as f:
        return json.load(f)


def _set_file_state(state_file: Path, **new_state: dict) -> None:
    state = _get_file_state(state_file)
    state.update(new_state)
    with state_file.open("w") as f:
        json.dump(state, f)


def _download_single(url: str, save_path: Path) -> None:
    # Check for partial file

    expected_size = _get_expected_size(url)
    headers = {}
    if save_path.exists():
        existing = save_path.stat().st_size

        if expected_size is not None and existing >= expected_size:
            eliot.log_message(f"File {url} already fully downloaded at {save_path}", level="debug")
            return

        headers["Range"] = f"bytes={existing}-"
        eliot.log_message(f"Resuming download for {url} from byte {existing}", level="debug")
    else:
        existing = 0

    # Request (with streaming)
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()

    if "Range" in headers and response.status_code != 206:
        eliot.log_message(
            f"Server did not support resuming download for {url}. Restarting from beginning.", level="debug"
        )
        existing = 0
        if save_path.exists():
            save_path.unlink()  # Delete existing partial file

    total_size = int(response.headers.get("content-length", 0)) + existing
    chunk_size = 1024 * 1024  # 1MB

    with (
        save_path.open("ab" if existing else "wb") as f,
        tqdm(
            total=total_size,
            initial=existing,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {url}",
            ascii=True,
        ) as bar,
    ):
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))


def _get_expected_size(url: str) -> int | None:
    response = requests.head(url, allow_redirects=True, timeout=10)
    if response.status_code != 200:
        return None
    content_length = response.headers.get("content-length")
    if content_length is None:
        return None
    return int(content_length)
