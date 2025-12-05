"""
Usage:
> > python -m misophonia_dataset.main --help

"""

# noqa: ANN201
from pathlib import Path

import eliot
import pandas as pd
import typer
from typing_extensions import Annotated

from ._binamix import download_sadie
from ._log import setup_print_logging
from .interface import SourceData, get_default_data_dir
from .misophonia_dataset import MisophoniaDataset
from .source_data.esc50 import Esc50Dataset
from .source_data.foams import FoamsDataset
from .source_data.fsd50k import Fsd50kDataset

setup_print_logging()

app = typer.Typer(help="Misophonia Dataset CLI")


@app.command()
def generate(
    datasets: Annotated[
        list[str], typer.Option("--source-dataset", "-d", help="Name(s) of source datasets use.")
    ] = None,
    base_save_dir: Annotated[Path, typer.Option("--datasets-dir", "-s", help="Directory to save datasets")] = None,
    num_samples: Annotated[int, typer.Option("--num-samples", "-n", help="Number of samples to generate")] = 1,
    splits: Annotated[list[str], typer.Option("--splits", "-p", help="Dataset splits to include")] = None,
    seed: Annotated[int, typer.Option("--random-seed", "-r", help="Random seed for sampling")] = 42,
) -> None:
    datasets = _get_default_datasets() if datasets is None or len(datasets) == 0 else datasets
    datasets = tuple(_get_dataset_from_name(name, base_dir=base_save_dir) for name in datasets)

    splits = ["train", "validation", "test"] if splits is None or len(splits) == 0 else splits

    misophonia_dataset = MisophoniaDataset(source_data=datasets)

    for split in splits:
        for sound in misophonia_dataset.generate(num_samples=num_samples, split=split, random_state=seed):
            print(sound)


@app.command()
def download(
    datasets: Annotated[list[str], typer.Argument(help="Name(s) of datasets to download.")] = None,
    base_save_dir: Annotated[Path, typer.Option("--datasets-dir", "-s", help="Directory to save datasets")] = None,
) -> None:
    """Downloads specified datasets."""
    if datasets is None or len(datasets) == 0:
        datasets = _get_default_datasets() + ("sadie",)

    eliot.log_message(f"Downloading datasets: {datasets}", level="debug")

    for dataset_name in datasets:
        if dataset_name.lower().strip() == "sadie":
            download_sadie()
            continue

        dataset = _get_dataset_from_name(dataset_name, base_dir=base_save_dir)

        if dataset.is_downloaded():
            eliot.log_message(f"Dataset {dataset_name} is already downloaded. Skipping.", level="info")
            continue

        eliot.log_message(f"Downloading dataset: {dataset_name}", level="info")
        dataset.download_data()
        eliot.log_message(f"Finished downloading dataset: {dataset_name}", level="info")


@app.command()
def search_metadata(
    q: Annotated[str, typer.Argument(help="Search query string in pandas query format.")],
    datasets: Annotated[list[str], typer.Argument(help="Name(s) of datasets to download.")] = None,
    base_save_dir: Annotated[Path, typer.Option("--datasets-dir", "-s", help="Directory to save datasets")] = None,
) -> None:
    """Search metadata in specified datasets."""
    eliot.log_message(f"Searching for '{q}' in datasets: {datasets}", level="info")

    metadata = []
    for dataset_name in datasets:
        dataset = _get_dataset_from_name(dataset_name, base_dir=base_save_dir)
        assert dataset.is_downloaded(), f"Dataset {dataset_name} is not downloaded yet."
        meta = dataset.get_metadata()
        metadata.append(meta)

    metadata = pd.concat(metadata, ignore_index=True)

    res = metadata.query(q)
    print(f"Found {len(res)} matching entries:")
    print(res)


def _get_dataset_from_name(name: str, base_dir: Path) -> SourceData:
    name = name.lower().strip()
    if name == "foams":
        return FoamsDataset(save_dir=get_default_data_dir(dataset_name="FOAMS", base_dir=base_dir))
    elif name == "esc50":
        return Esc50Dataset(save_dir=get_default_data_dir(dataset_name="ESC50", base_dir=base_dir))
    elif name == "fsd50k":
        return Fsd50kDataset(save_dir=get_default_data_dir(dataset_name="FSD50K", base_dir=base_dir))
    raise ValueError(f"Unknown dataset name: {name}")


def _get_default_datasets() -> tuple[str]:
    return ("foams", "esc50", "fsd50k")


if __name__ == "__main__":
    app()
