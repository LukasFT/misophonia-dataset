import hashlib
import urllib.request
import zipfile
from pathlib import Path

import datasets


def get_foams_dataset(download_dir: Path = Path("./data/FOAMS")) -> datasets.Dataset:
    """
    Download (if needed), extract (if needed), and return the FOAMS processed-audio dataset
    as a Hugging Face `datasets.Dataset` using the `audiofolder` builder.

    Source:
      - FOAMS: Processed Audio Files @ Zenodo (record 7109069)
        Files: FOAMS_processed_audio.zip (md5: 89e717006cea3687384baa3c86d6307c),
               segmentation_info.csv (optional)  :contentReference[oaicite:0]{index=0}

    Returns:
      datasets.Dataset with an `audio` column (cast to 44.1 kHz) and a `path` column.

    Notes:
      - If you need the pilot bundle instead, swap the URLs for Zenodo record 8170180
        (file: Pilot_sound_stimuli.zip). :contentReference[oaicite:1]{index=1}
    """
    download_dir = Path(download_dir).expanduser().resolve()

    audio_zip_url = "https://zenodo.org/records/8170225/files/FOAMS_processed_audio.zip?download=1"
    audio_zip_md5 = "89e717006cea3687384baa3c86d6307c"
    audio_zip_path = download_dir / "FOAMS_processed_audio.zip"

    seg_csv_url = "https://zenodo.org/records/8170225/files/segmentation_info.csv?download=1"
    seg_csv_md5 = "0ac1de8a66ffb52be34722ad8cd5e514"
    seg_csv_path = download_dir / "segmentation_info.csv"

    if not audio_zip_path.exists():
        _download(audio_zip_url, audio_zip_path, audio_zip_md5)

    if not seg_csv_path.exists():
        _download(seg_csv_url, seg_csv_path, seg_csv_md5)

    # 3) Extract if needed
    extract_to_dir = download_dir / "FOAMS_processed_audio"  # Will contain the extracted files
    if not download_dir.exists() or not any(download_dir.rglob("*.wav")):
        download_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(audio_zip_path) as zf:
            zf.extractall(download_dir)

    # 4) Load as HF Dataset via the generic "audiofolder" builder
    # This will infer a split if subfolders are present; otherwise a single split "train".
    ds = datasets.load_dataset("audiofolder", data_dir=str(extract_to_dir))["train"]

    # Ensure consistent sampling rate for our pipeline
    # ds = ds.cast_column(
    #     "audio", datasets.Audio(sampling_rate=44100)
    # )  # FOAMS was prepared at 44.1 kHz according to FOAMS_documentation.pdf

    # Add an explicit file path column for downstream joins if not already present
    if "path" not in ds.column_names and "file" not in ds.column_names:
        # the "audio" feature stores {"path": "...", "array": ..., "sampling_rate": ...}
        def _add_path(example):  # noqa: ANN001, ANN202
            p = example["audio"]["path"]
            example["path"] = p if isinstance(p, str) else ""
            return example

        ds = ds.map(_add_path, desc="Adding file path column")

    return ds


def _md5(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute md5 of a file."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path, md5: str | None = None) -> None:
    """Download a URL to dest (atomic-ish)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        urllib.request.urlretrieve(url, tmp)  # nosec - plain HTTP GET only
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    if md5 is not None:
        actual_md5 = _md5(dest)
        if actual_md5 != md5:
            raise ValueError(f"Checksum mismatch for {dest.name}: {actual_md5} != {md5}")


if __name__ == "__main__":
    ds = get_foams_dataset()
    print(ds)
    print(ds[0])
