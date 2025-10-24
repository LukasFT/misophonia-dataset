import os
import pandas as pd
import json
import argparse
import shutil

fsd50k_to_foams = "../data/fsd50k_to_foams_mapping.json"
fsd50k_metadata = "../data/metadata/FSD50K.metadata/collection/collection_dev.csv"

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
    fsd_50k['labels'] = fsd_50k['labels']
    return fsd_50k



# save only samples with trigger sounds
def fsd50k_triggers(fsd_50k: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
        Filters the FSD50K DataFrame to include only samples with trigger sounds.
        Args:
            fsd_50k (pd.DataFrame): DataFrame containing the FSD50K metadata.
            mapping (dict): Dictionary mapping FSD50K classes to FOAMS trigger classes, saved as fsd50k_to_foams_mapping.json
        Returns:
            pd.DataFrame: DataFrame containing only the samples with trigger sounds.
    """
    trigger_classes = [k for k in mapping["Trigger"].keys()]
    fsd_50k_triggers = fsd_50k[fsd_50k['labels'].isin(trigger_classes)]
    fsd_50k_triggers.loc[:, "labels"] = fsd_50k_triggers['labels'].apply(lambda x: mapping["Trigger"][str(x)]["foams_mapping"])
    return fsd_50k_triggers

# Copy S
def copy_samples(meta_df: pd.DataFrame, source_dir: str, target_dir : str = "../data/FSD50K"):
    """
        Copies audio samples from the source directory to the target directory based on the metadata DataFrame.
        Args:
            meta_df (pd.DataFrame): DataFrame containing the metadata of the samples to be copied.
            source_dir (str): Path to the source directory containing the audio samples.
            target_dir (str): Path to the target directory where the samples will be copied.
    """
    os.makedirs(target_dir, exist_ok=True)
    for _, row in meta_df.iterrows():
        src_path = os.path.join(source_dir, str(row['fname']) + ".wav")
        dst_path = os.path.join(target_dir, str(row['fname']) + ".wav")
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)

def save_metadata(meta_df: pd.DataFrame, target_path: str = "../data/metadata/fsd50k_triggers_metadata.csv"):
    """ 
        Saves the metadata DataFrame to a CSV file.
        Args:
            meta_df (pd.DataFrame): DataFrame containing the metadata to be saved.
            target_path (str): Path to the target CSV file.
    """
    meta_df.to_csv(target_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_dir', type=str, required=True, help='Path to FSD50K audio files')
    parser.add_argument('--target_dir', type=str, required=True, default="../data/FSD50K", help='Path to save filtered FSD50K audio files')
    parser.add_argument('--metadata_path', type=str, required=True, default="../data/metadata/fsd50k_triggers_metadata.csv", help='Path to save filtered FSD50K metadata CSV')
    parser.add_argument('--is_eval', type=bool, required=True, default=False, help='Generate samples from eval (True) or dev (False) set')

    args = parser.parse_args()

    # Change metadata path if eval set is chosen.
    if args.is_eval:
        fsd50k_metadata = "../data/metadata/FSD50K.metadata/collection/collection_eval.csv"

    print("Loading FSD50K metadata...")
    fsd_50k = load_fsd50k(fsd50k_metadata)
    with open(fsd50k_to_foams, 'r') as f:
        data = json.load(f)

    print("Filtering FSD50K for trigger sounds...")
    fsd_50k_triggers = fsd50k_triggers(fsd_50k, data)
    print(f"Number of trigger samples found: {fsd_50k_triggers.shape[0]}")

    print("Copying trigger samples...")
    copy_samples(fsd_50k_triggers, source_dir=args.source_dir, target_dir=args.target_dir)

    print("Saving metadata...")
    save_metadata(fsd_50k_triggers, target_path=args.metadata_path)