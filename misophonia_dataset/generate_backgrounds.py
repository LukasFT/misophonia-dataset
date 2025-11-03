import os
import pandas as pd
import json
import argparse
import shutil
import wave

fsd50k_metadata = "../data/metadata/FSD50K.metadata/collection/collection_dev.csv"
path = "../data/FSD50K.dev_audio/"


# load fsd 50k metadata
def load_fsd50k(filepath: str) -> pd.DataFrame:
    """
    Loads the FSD50K metadata from a CSV file.
    Args:
        filepath (str): Path to the CSV file containing FSD50K metadata.
    Returns:
        pd.DataFrame: DataFrame containing the FSD50K metadata.
    """
    fsd_50k = pd.read_csv(filepath_or_buffer=filepath)
    fsd_50k["labels"] = fsd_50k["labels"]
    return fsd_50k


# save only samples with background sounds
def fsd50k_backgrounds(fsd_50k: pd.DataFrame, background_classes: list[str], path: str) -> pd.DataFrame:
    """
    Filters the FSD50K DataFrame to include only samples with background sounds.
    Args:
        fsd_50k (pd.DataFrame): DataFrame containing the FSD50K metadata.
        background_classes (list[str]): List of background classes to sample form
        path (str): path to the folder containing wav files
    Returns:
        pd.DataFrame: DataFrame containing only the samples with background sounds.
    """
    backgrounds = fsd_50k[fsd_50k["labels"].isin(background_classes)]
    print("Number of backgrounds before filtering: ", backgrounds.shape[0])
    durations = []
    for _, row in backgrounds.iterrows():
        filename = str(row.get("fname")) + ".wav"
        if not filename:
            durations.append(None)
            continue

        wav_path = os.path.join(path, filename)
        if not os.path.exists(wav_path):
            durations.append(None)
            continue

        try:
            with wave.open(wav_path, "r") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                durations.append(duration)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            durations.append(None)

    backgrounds["Duration"] = durations

    return backgrounds[backgrounds["Duration"] > 7]


# Copy S
def copy_samples(meta_df: pd.DataFrame, source_dir: str, target_dir: str = "../data/background_dev"):
    """
    Copies audio samples from the source directory to the target directory based on the metadata DataFrame.
    Args:
        meta_df (pd.DataFrame): DataFrame containing the metadata of the samples to be copied.
        source_dir (str): Path to the source directory containing the audio samples.
        target_dir (str): Path to the target directory where the samples will be copied.
    """
    os.makedirs(target_dir, exist_ok=True)
    for _, row in meta_df.iterrows():
        src_path = os.path.join(source_dir, str(row["fname"]) + ".wav")
        dst_path = os.path.join(target_dir, str(row["fname"]) + ".wav")
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)


def save_metadata(meta_df: pd.DataFrame, target_path: str = "../data/metadata/backgrounds_metadata.csv"):
    """
    Saves the metadata DataFrame to a CSV file.
    Args:
        meta_df (pd.DataFrame): DataFrame containing the metadata to be saved.
        target_path (str): Path to the target CSV file.
    """
    meta_df.to_csv(target_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=str, required=True, help="Path to FSD50K audio files")
    parser.add_argument(
        "--target_dir",
        type=str,
        default="../data/backgrounds_dev",
        help="Path to save filtered FSD50K audio files",
    )
    parser.add_argument(
        "--metadata_path",
        type=str,
        default="../data/metadata/backgrounds_metadata.csv",
        help="Path to save filtered FSD50K metadata CSV",
    )
    parser.add_argument(
        "--is_eval",
        type=str,
        default="No",
        help="Generate samples from eval (True) or dev (False) set",
    )

    args = parser.parse_args()

    # Change metadata path if eval set is chosen.
    if args.is_eval == "Yes":
        fsd50k_metadata = "../data/metadata/FSD50K.metadata/collection/collection_eval.csv"
        path = "../data/FSD50K.eval_audio/"

    # Load background classes
    with open("../data/background_classes.json", "r") as f:
        data = json.load(f)
        background_classes = data["Backgrounds"]

    print("Loading FSD50K metadata...")
    fsd_50k = load_fsd50k(fsd50k_metadata)

    print("Filtering FSD50K for background sounds...")
    fsd_50k_backgrounds = fsd50k_backgrounds(fsd_50k, background_classes, path)
    print(f"Number of background samples found: {fsd_50k_backgrounds.shape[0]}")

    print("Copying background samples...")
    copy_samples(fsd_50k_backgrounds, source_dir=args.source_dir, target_dir=args.target_dir)

    print("Saving metadata...")
    save_metadata(fsd_50k_backgrounds, target_path=args.metadata_path)
