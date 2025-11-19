import hashlib
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
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
