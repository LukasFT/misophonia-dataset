import itertools
from abc import ABC, abstractmethod
from collections.abc import Collection
from pathlib import Path
from typing import Literal, TypeAlias

import numpy as np
import pydantic

MappingT: TypeAlias = dict[str, dict[Literal["foams_mapping"], str]]
"""The structure of a mapping from dataset-specific classes to FOAMS classes."""


SplitT: TypeAlias = Literal["train", "val", "test"]
"""The possible dataset splits."""


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,  # this means that instances are immutable
        extra="forbid",  # Do not allow extra fields
    )


class License(BaseModel):
    license_url: str
    attribution_name: str
    attribution_url: str


class SourceDataItem(BaseModel):
    split: SplitT
    """Dataset split: train, val, or test. See SplitT."""
    source_dataset: str
    """Name of the source dataset that returned this metadata."""
    file_path: Path
    """Path to the audio file."""
    freesound_id: int | None = None
    """FreeSound.org ID of the audio file, if available."""
    label_type: Literal["control", "trigger", "background"]
    """Type of sound."""
    labels: tuple[str, ...]
    """
    Label according to the FOAMS taxonomy (if sound_type = 'trigger') and, otherwise, the AudioSet (FSD50K) taxonomy.

    There can be one more more labels (str or list of str). But all labels must be of the same sound_type. Any data point that has labels from multiple sound_types should be excluded.
    """
    validated_by: tuple[str, ...] | None = None
    """List of names for studies (e.g., FOAMS) that have validated this data point. If not any, None. Only applicable for trigger sounds."""
    licensing: tuple[License, ...] | None = None
    """Licensing information. A collection of dictionaries (see LicenceT above)."""

    model_config = pydantic.ConfigDict(
        # Allow extra fields since different datasets have different metadata fields. Extra fields should be prefixed by the dataset name to avoid conflicts.
        extra="allow",
    )


import random


class SourceTrack(BaseModel):
    source_item: SourceDataItem

    start: int
    """Start time (in samples, i.e. not time) of the clip."""
    end: int
    """End time (in samples, i.e. not time) of the clip."""

    azimuth: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))
    elevation: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))
    level: float = pydantic.Field(default_factory=lambda: round(random.uniform(0.4, 1.0), 1))
    reverb: float = pydantic.Field(
        default_factory=lambda: round(random.uniform(0.0, 1.0), 1)  # TODO: What should be the default?
    )


class GlobalMixingParams(BaseModel):
    subject_id: str  # Randomized default
    speaker_layout: str = "none"  # Stereo
    sample_rate: int = 44100
    reverb_type: str  # Randomized default
    mode: str = "nearest"
    ir_type: str = "BRIR"

    # Initilize defaults at random
    @pydantic.model_validator(mode="before")
    @classmethod
    def fill_defaults(cls, values: list):  # noqa: ANN001, ANN206
        rng: np.random.Generator = values.pop("_rng", np.random.default_rng())

        if "subject_id" not in values:
            values["subject_id"] = rng.choice(
                [
                    "D1",
                    "D2",
                    "H3",
                    "H4",
                    "H5",
                    "H6",
                    "H7",
                    "H8",
                    "H9",
                    "H10",
                    "H11",
                    "H12",
                    "H13",
                    "H14",
                    "H15",
                    "H16",
                    "H17",
                    "H18",
                    "H19",
                    "H20",
                ]
            )

        if "reverb_type" not in values:
            values["reverb_type"] = rng.choice(["1", "2", "3", "4"])

        return values


DEFAULT_MIXED_DATASET_LICENSE = (
    License(
        license_url="https://creativecommons.org/licenses/by/4.0/",  # Figure out if that is the license we want
        attribution_name="Lukas Frimer Tholander & Tonio Ermakoff",
        attribution_url="https://github.com/LukasFT/misophonia-dataset",
    ),
    License(  # For the SADIE Database
        license_url="https://www.apache.org/licenses/LICENSE-2.0/",
        attribution_name="C. Armstrong, L. Thresh & G. Kearney",
        attribution_url="https://www.mdpi.com/2076-3417/8/11/2029",
    ),
)


class MisophoniaItem(BaseModel):
    split: SplitT

    uuid: str | None = None

    is_trigger: bool
    foreground_categories: tuple[str, ...]
    background_categories: tuple[str, ...]

    mix: np.ndarray | Path
    """Binaural mixed audio data for both foreground and background sounds."""
    ground_truth: np.ndarray | Path | None
    """Ground truth audio data. If available, this is the isolated binaural audio for the trigger sound."""
    length: int
    """Duration in number of samples."""

    foregrounds: tuple[SourceTrack, ...]
    backgrounds: tuple[SourceTrack, ...]

    global_mixing_params: GlobalMixingParams

    mix_licensing: tuple[License, ...] = DEFAULT_MIXED_DATASET_LICENSE

    @property
    def trigger_categories(self) -> tuple[str, ...] | None:
        return self.foreground_categories if self.is_trigger else None

    @property
    def duration(self) -> float:
        return self.length / self.global_mixing_params.sample_rate

    # Validate that all forgrounds and background are of split
    @pydantic.model_validator(mode="after")
    def check_splits(self) -> "MisophoniaItem":
        if any(track.source_item.split != self.split for track in itertools.chain(self.foregrounds, self.backgrounds)):
            raise ValueError("All foreground and background items must match the MisophoniaItem split.")
        return self


def get_default_data_dir(*, dataset_name: str | None = None, base_dir: Path | None = None) -> Path:
    base_dir = base_dir or Path(__file__).parent.parent / "data"
    if dataset_name is None:
        return base_dir
    return base_dir / dataset_name


class SourceData(ABC):
    @abstractmethod
    def is_downloaded(self) -> bool:
        """
        Checks if the dataset has already been downloaded.

        Returns:
            True if the dataset is downloaded, False otherwise.
        """
        pass

    @abstractmethod
    def download_data(self) -> None:
        """
        Downloads dataset, extracts it, and saves it into the specified directory.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Collection[SourceDataItem]:
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Deletes the entire dataset. Useful after mixing sounds.
        """
        pass

    def __str__(self) -> str:
        return f"<SourceData: {self.__class__.__name__}>"
