"""
Usage:
> > python -m misophonia_dataset.main --help

"""

# noqa: ANN201
from pathlib import Path

import eliot
import typer
from typing_extensions import Annotated

from ._log import setup_print_logging
from .interface import SourceData, get_default_data_dir
from .source_data.esc50 import Esc50Dataset
from .source_data.foams import FoamsDataset
from .source_data.fsd50k import Fsd50kDataset

setup_print_logging()

app = typer.Typer(help="Misophonia Dataset CLI")


@app.command()
def download(
    datasets: Annotated[list[str], typer.Argument(help="Name(s) of datasets to download.")] = None,
    base_save_dir: Annotated[Path, typer.Option("--save-dir", "-s", help="Directory to save datasets")] = None,
) -> None:
    """Downloads specified datasets."""
    if datasets is None or len(datasets) == 0:
        datasets = ["foams", "esc50", "fsd50k"]

    eliot.log_message(f"Downloading datasets: {datasets}", level="debug")

    for dataset_name in datasets:
        dataset = _get_dataset_from_name(dataset_name, base_dir=base_save_dir)

        if dataset.is_downloaded():
            eliot.log_message(f"Dataset {dataset_name} is already downloaded. Skipping.", level="info")
            continue

        eliot.log_message(f"Downloading dataset: {dataset_name}", level="info")
        dataset.download_data()
        eliot.log_message(f"Finished downloading dataset: {dataset_name}", level="info")


@app.command()
def placeholder() -> None:
    """Placeholder command to ensure CLI has multiple commands."""
    pass


def _get_dataset_from_name(name: str, base_dir: Path) -> SourceData:
    name = name.lower().strip()
    if name == "foams":
        return FoamsDataset(save_dir=get_default_data_dir(dataset_name="FOAMS", base_dir=base_dir))
    elif name == "esc50":
        return Esc50Dataset(save_dir=get_default_data_dir(dataset_name="ESC50", base_dir=base_dir))
    elif name == "fsd50k":
        return Fsd50kDataset(save_dir=get_default_data_dir(dataset_name="FSD50K", base_dir=base_dir))
    raise ValueError(f"Unknown dataset name: {name}")


if __name__ == "__main__":
    app()
