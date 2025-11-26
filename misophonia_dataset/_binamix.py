import subprocess
import sys
from pathlib import Path
import os

from .source_data._downloading import download_and_unzip


def get_binamix_dir() -> Path:
    return Path(__file__).parent.parent / "Binamix"


def setup_binamix_import() -> None:
    binamix_repo = get_binamix_dir()

    if not any(binamix_repo.iterdir()):  # Binamix dir is empty
        print("Warning: Binamix repository is empty. Updating submodule...")
        subprocess.run(["git", "submodule", "update", "--init"], check=True)

    sys.path.append(str(binamix_repo))


def setup_binamix() -> None:
    """Adds the Binamix library to the system path for importing."""
    # TODO: Help Binamix distribute their package on PyPi or similar
    setup_binamix_import()

    try:
        import binamix  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError("Failed to import Binamix after adding to path.") from e

    downloaded_sadie = False
    try:
        import binamix.sadie_utilities  # type: ignore
    except FileNotFoundError as e:
        if "SADIE" in str(e):
            print("Warning: Binamix SADIE database not found. Downloading it.")
            # binamix_repo = get_binamix_dir()
            # This should work but the files 404 (per November 26, 2025):
            # subprocess.run([sys.executable, "-m", "binamix.sadie_db_setup"], cwd=binamix_repo, check=True)
            _download_sadie()
            downloaded_sadie = True

    if downloaded_sadie:
        try:
            import binamix.sadie_utilities  # type: ignore  # noqa: F401
        except FileNotFoundError as e:
            if "SADIE" in str(e):
                raise FileNotFoundError(
                    "Failed to find SADIE database even after downloading. Please check Binamix setup."
                ) from e


def _download_sadie() -> None:
    binamix_repo = get_binamix_dir()
    data_specs = {
        "D1": (  # TODO: These files are not enough to make Binamix work ...
            {
                "url": "https://zenodo.org/records/10886409/files/D1.zip?download=1",
                "md5": "468f0fce29c2f5880627c571b73e64c3",
            },
        ),
        "D2": (
            {
                "url": "https://zenodo.org/records/12092466/files/D2.zip?download=1",
                "md5": "0564133299f118fe2731f6d65abbd8f8",
            },
        ),
    }
    for subject_id, specs in data_specs.items():
        print(f"Downloading SADIE data for subject {subject_id}...")
        download_and_unzip(
            specs,
            save_dir=os.path.join(binamix_repo, "sadie", "Database-Master_V1-4"),
            rename_extracted_dir=subject_id,
        )


if __name__ == "__main__":
    setup_binamix()
