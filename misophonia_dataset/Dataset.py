# class for each of the datasets
#   fields:
#       - metadata path. Metadata needs "Trig" columns (1=trigger, 0=control, -1=background)
#       - directory path.
#       - column name for class lable in metadata path
#       - metadata NEEDS to include duration and amplitude
#
# MisoDataset takes X amount of datasets, splits each into train/test/val (splitting respectively
# controls, triggers, and backgrounds). Combines each into a joint train/test/val, and then applies the mixing pipeline.
#
import pandas as pd
import os


class MisoDataset(Dataset):
    def __init__(
        self,
        datasets: List[Dataset],
        target_dir="../data/miso_dataset/",
    ):
        assert len(dataset_names) == len(meta_paths) == len(dir_paths)

        self.dataset_names = dataset_names
        self.meta_paths = {dataset_names[i]: m for i, m in enumerate(meta_paths)}

    def train_val_test_split(dataset_name, meta_path, dir_path):
        """
        Apply train/val/test split to a dataset given a metadata
        """
        meta_df = pd.read_csv(meta_path)

        triggers = meta_df[meta_df["Trig"] == 1]
        controls = meta_df[meta_df["Trig"] == 0]
        backgrounds = meta_df[meta_df["Trig"] == -1]

class Dataset:
    def __init__(self,
               download_url: str,
               meta_url: str,
               class_column: str,
    ):
        