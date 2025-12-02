import random
from pathlib import Path

import librosa
import numpy as np
from pydantic import BaseModel, Field

from ._binamix import setup_binamix

setup_binamix()
from binamix.sadie_utilities import TrackObject, mix_tracks_binaural  # type: ignore


class MixingParams(BaseModel):
    # spatial placement (example ranges, adjust as needed)
    fg_azimuth: float = Field(default_factory=lambda: random.randint(-180, 180))
    fg_elevation: float = Field(default_factory=lambda: random.randint(-180, 180))

    bg_azimuth: float = Field(default_factory=lambda: random.randint(-180, 180))
    bg_elevation: float = Field(default_factory=lambda: random.randint(-180, 180))

    # audio gain
    fg_level: float = Field(default_factory=lambda: round(random.uniform(0.4, 1.0), 1))

    # metadata
    subject_id: int = Field(default_factory=lambda: random.choice(["D1", "D2"]))
    speaker_layout: str = "none"
    sr: int = 44100

    # reverb selection (chooses one of 1–4 as string)
    reverb_type: str = Field(default_factory=lambda: random.choice(["1", "2", "3", "4"]))


def pad_and_normalize_audio_files(fg_audio: np.ndarray, bg_audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Normalize volume using rms
    rms_fg = np.sqrt(np.mean(fg_audio**2))
    rms_bg = np.sqrt(np.mean(bg_audio**2))

    rms_target = rms_fg + rms_bg / 2

    fg_audio *= rms_target / rms_fg
    bg_audio *= rms_target / rms_bg

    len1 = len(fg_audio)
    len2 = len(bg_audio)

    # If already equal length, return unchanged
    if len1 == len2:
        return fg_audio, bg_audio

    if len1 < len2:
        short, long_ = fg_audio, bg_audio
        swap = True
    else:
        short, long_ = bg_audio, fg_audio
        swap = False

    # Pad random amount
    needed = len(long_) - len(short)
    start = np.random.randint(0, needed)  # noqa: NPY002
    end = needed - start

    # Perform padding
    padded = np.concatenate([np.zeros(start, dtype=short.dtype), short, np.zeros(end, dtype=short.dtype)])

    # Return in original order
    if swap:
        return padded, long_
    else:
        return long_, padded


def validation_binaural_mix(
    trig: Path,
    control: Path,
    bg: Path,
) -> tuple[tuple[np.darray, np.ndarray, int], tuple[np.ndarray, np.ndarray, int]]:
    """
    Mixing function specially designed for the validation experiment. Guarantees (trig, bg) (ctrl, bg) pairs with equivalent
    mixing parameters.

    Returns mixed (trig, bg), (ctrl, bg) and ground truths + sample rates for each mix.
    """
    params = MixingParams()

    t_mix, t_gt, t_sr = binaural_mix(
        trig,
        bg,
        params,
        is_trig=True,
    )

    c_mix, c_gt, c_sr = binaural_mix(
        trig,
        bg,
        params,
        is_trig=False,
    )

    return (t_mix, t_gt, t_sr), (c_mix, c_gt, c_sr)


def binaural_mix(
    fg: Path,
    bg: Path,
    params: MixingParams,
    *,
    is_trig: bool,
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Max a binaural mix of a foreground (trigger) and background sound.

    Params:
        fg (Path): path to foreground audio file
        bg (Path): path to background audio file

    Returns:
        mix (np.ndarray): binaural mixed audio
        sr (int): sample rate of mixed audio
    """
    ir_type = "BRIR"

    # MIXING
    fg_audio, _ = librosa.load(params.fg, sr=params.sr, mono=True)
    bg_audio, _ = librosa.load(params.bg, sr=params.sr, mono=True)

    fg_padded, bg_padded = pad_and_normalize_audio_files(fg_audio, bg_audio)

    fg_track = TrackObject(
        name="trigger",
        azimuth=params.fg_azimuth,
        elevation=params.fg_elevation,
        level=params.fg_level,
        reverb=0.0,
        audio=fg_padded,
    )
    bg_track = TrackObject(
        name="background",
        azimuth=params.bg_azimuth,
        elevation=params.bg_elevation,
        level=0.7,
        reverb=0.0,
        audio=bg_padded,
    )

    mix = mix_tracks_binaural(
        [fg_track, bg_track],
        params.subject_id,
        params.sr,
        ir_type,
        params.speaker_layout,
        mode="nearest",
        reverb_type=params.reverb_type,
    )

    if is_trig:
        return mix, fg_padded, params.sr
    else:
        return mix, np.zeros(fg_padded.shape[0]), params.sr  # silence for control sound
