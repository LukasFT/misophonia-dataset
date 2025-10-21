import os
import pandas as pd
import json
import argparse
import shutil

esc50_to_foams = "../data/esc50_to_foams_mapping.json"
esc50_metadata = "../data/metadata/esc50.csv"


# load fsd 50k metadata
def load_esc50(filepath: str) -> pd.DataFrame:
    """
    Loads the FSD50K metadata from a CSV file.
    Args:
        filepath (str): Path to the CSV file containing FSD50K metadata.
    Returns:
        pd.DataFrame: DataFrame containing the FSD50K metadata.
    """
    esc50 = pd.read_csv(filepath_or_buffer=filepath)
    return esc50


# save only samples with trigger sounds
def esc50_triggers(esc50: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Filters the FSD50K DataFrame to include only samples with trigger sounds.
    Args:
        esc50 (pd.DataFrame): DataFrame containing the FSD50K metadata.
        mapping (dict): Dictionary mapping FSD50K classes to FOAMS trigger classes, saved as fsd50k_to_foams_mapping.json
    Returns:
        pd.DataFrame: DataFrame containing only the samples with trigger sounds.
    """
    trigger_classes = [k for k in mapping.keys()]
    esc50_triggers = esc50[esc50["category"].isin(trigger_classes)]
    esc50_triggers.loc[:, "category"] = esc50_triggers["category"].apply(lambda x: mapping[str(x)]["foams_mapping"])
    return esc50_triggers


# Copy S
def copy_samples(meta_df: pd.DataFrame, source_dir: str, target_dir: str = "../data/ESC-50/"):
    """
    Copies audio samples from the source directory to the target directory based on the metadata DataFrame.
    Args:
        meta_df (pd.DataFrame): DataFrame containing the metadata of the samples to be copied.
        source_dir (str): Path to the source directory containing the audio samples.
        target_dir (str): Path to the target directory where the samples will be copied.
    """
    os.makedirs(target_dir, exist_ok=True)
    for _, row in meta_df.iterrows():
        src_path = os.path.join(source_dir, str(row["filename"]))
        dst_path = os.path.join(target_dir, str(row["filename"]))
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)


def save_metadata(meta_df: pd.DataFrame, target_path: str = "../data/metadata/esc50_triggers_metadata.csv"):
    """
    Saves the metadata DataFrame to a CSV file.
    Args:
        meta_df (pd.DataFrame): DataFrame containing the metadata to be saved.
        target_path (str): Path to the target CSV file.
    """
    meta_df.to_csv(target_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=str, required=True, help="Path to ESC50 audio files")

    args = parser.parse_args()

    print("Loading ESC50 metadata...")
    esc50 = load_esc50(esc50_metadata)
    with open(esc50_to_foams, "r") as f:
        data = json.load(f)

    print("Filtering ESC50 for trigger sounds...")
    esc50_triggers = esc50_triggers(esc50, data)
    print(f"Number of trigger samples found: {esc50_triggers.shape[0]}")

    print("Copying trigger samples...")
    copy_samples(esc50_triggers, source_dir=args.source_dir, target_dir="../data/ESC-50/")

    print("Saving metadata...")
    save_metadata(esc50_triggers, target_path="../data/metadata/esc50_triggers_metadata.csv")
