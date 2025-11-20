import hashlib
import os
import random
import time
from pathlib import Path
from urllib.parse import urlparse

import librosa
import numpy as np
import requests
from tqdm import tqdm

# Import Binamix
curr_dir = os.getcwd()
binamix_dir = "/workspaces/misophonia-dataset/Binamix"
if curr_dir != binamix_dir:
    os.chdir("/workspaces/misophonia-dataset/Binamix")
from binamix.sadie_utilities import TrackObject, mix_tracks_binaural

os.chdir(curr_dir)


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


def pad_audio_files(fg_audio: np.ndarray, bg_audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    len1 = len(fg_audio)
    len2 = len(bg_audio)

    # If already equal length, return unchanged
    if len1 == len2:
        return fg_audio, bg_audio

    if len1 < len2:
        short, long_ = fg_audio, bg_audio
        swap = True
    else:
        short, long_ = bg_audio, fg_audio
        swap = False

    # Pad random amount
    needed = len(long_) - len(short)
    start = np.random.randint(0, needed)  # noqa: NPY002
    end = needed - start

    # Perform padding
    padded = np.concatenate([np.zeros(start, dtype=short.dtype), short, np.zeros(end, dtype=short.dtype)])

    # Return in original order
    if swap:
        return padded, long_
    else:
        return long_, padded


def binaural_mix(fg: Path, bg: Path) -> np.ndarray:
    # Deterministic Params
    subject_id = "D2"
    ir_type = "BRIR"

    # Randomized Params
    speaker_layout = "none"
    sr = 44100
    fg_azimuth = random.randint(-180, 180)
    fg_elevation = random.randint(-180, 180)
    bg_azimuth = random.randint(-180, 180)
    bg_elevation = random.randint(-180, 180)

    # MIXING
    fg_audio, _ = librosa.load(fg, sr=sr, mono=True)
    bg_audio, _ = librosa.load(bg, sr=sr, mono=True)

    fg_padded, bg_padded = pad_audio_files(fg_audio, bg_audio)

    fg_track = TrackObject(
        name="trigger", azimuth=fg_azimuth, elevation=fg_elevation, level=0.6, reverb=0.0, audio=fg_padded
    )
    bg_track = TrackObject(
        name="background", azimuth=bg_azimuth, elevation=bg_elevation, level=0.6, reverb=0.0, audio=bg_padded
    )

    mix = mix_tracks_binaural(
        [fg_track, bg_track], subject_id, sr, ir_type, speaker_layout, mode="nearest", reverb_type="1"
    )

    return mix, sr
