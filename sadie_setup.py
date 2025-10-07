#!/usr/bin/env python3
import os
import sys
import requests
from zipfile import ZipFile

# URLs for D1 and D2 full subject ZIPs
URLS = {
    "D1": "https://www.york.ac.uk/sadie-project/Resources/SADIEIIDatabase/D1.zip",
    "D2": "https://www.york.ac.uk/sadie-project/Resources/SADIEIIDatabase/D2.zip",
}


def download_file(url, dest_path):
    """Download a file with streaming and resume support."""
    temp_path = dest_path + ".part"
    headers = {}
    if os.path.exists(temp_path):
        existing = os.path.getsize(temp_path)
        headers["Range"] = f"bytes={existing}-"
    else:
        existing = 0

    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        mode = "ab" if existing else "wb"
        with open(temp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    os.rename(temp_path, dest_path)


def extract_zip(zip_path, extract_dir):
    """Extract a zip file to a directory."""
    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)


def ensure_sadie_data(dest_dir):
    """Download and extract D1 and D2 datasets if missing."""
    os.makedirs(dest_dir, exist_ok=True)

    for name, url in URLS.items():
        zip_path = os.path.join(dest_dir, f"{name}.zip")
        extract_dir = os.path.join(dest_dir, name)

        if os.path.isdir(extract_dir):
            print(f"✅ {name} already extracted, skipping.")
            continue
        if os.path.isfile(zip_path):
            print(f"📦 {name}.zip already exists, skipping download.")
        else:
            print(f"⬇️  Downloading {name}...")
            download_file(url, zip_path)
            print(f"✅ Downloaded {name}.zip")

        print(f"📂 Extracting {name}...")
        extract_zip(zip_path, extract_dir)
        print(f"✅ Extracted to {extract_dir}")
        os.remove(zip_path)
        print(f"🧹 Removed {zip_path}")


if __name__ == "__main__":
    destination = "Binamix/sadie/Database-Master_V1-4"
    ensure_sadie_data(destination)
    print(f"\n🎉 All done! Files are in: {destination}")
