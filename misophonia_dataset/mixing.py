import random
import sys
from pathlib import Path

import librosa
import numpy as np

sys.path.append(str(Path(__file__).parent.parent / "Binamix"))

from binamix.sadie_utilities import TrackObject, mix_tracks_binaural


def pad_audio_files(fg_audio: np.ndarray, bg_audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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


def binaural_mix(fg: Path, bg: Path) -> np.ndarray:
    # Deterministic Params
    subject_id = "D2"
    ir_type = "BRIR"

    # Randomized Params
    speaker_layout = "none"
    sr = 44100
    fg_azimuth = random.randint(-180, 180)
    fg_elevation = random.randint(-180, 180)
    bg_azimuth = random.randint(-180, 180)
    bg_elevation = random.randint(-180, 180)

    # MIXING
    fg_audio, _ = librosa.load(fg, sr=sr, mono=True)
    bg_audio, _ = librosa.load(bg, sr=sr, mono=True)

    fg_padded, bg_padded = pad_audio_files(fg_audio, bg_audio)

    fg_track = TrackObject(
        name="trigger", azimuth=fg_azimuth, elevation=fg_elevation, level=0.6, reverb=0.0, audio=fg_padded
    )
    bg_track = TrackObject(
        name="background", azimuth=bg_azimuth, elevation=bg_elevation, level=0.6, reverb=0.0, audio=bg_padded
    )

    mix = mix_tracks_binaural(
        [fg_track, bg_track], subject_id, sr, ir_type, speaker_layout, mode="nearest", reverb_type="1"
    )

    return mix, sr
