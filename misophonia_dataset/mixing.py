import random
from pathlib import Path
from typing import List

import librosa
import numpy as np
import pydantic

from ._binamix import setup_binamix

setup_binamix()
from binamix.sadie_utilities import TrackObject, mix_tracks_binaural  # type: ignore


class MixingParams(pydantic.BaseModel):
    # spatial placement (example ranges, adjust as needed)
    fg_azimuth: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))
    fg_elevation: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))

    bg_azimuth: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))
    bg_elevation: float = pydantic.Field(default_factory=lambda: random.randint(-180, 180))

    # audio gain
    fg_level: float = pydantic.Field(default_factory=lambda: round(random.uniform(0.4, 1.0), 1))

    # metadata
    subject_id: str = pydantic.Field(default_factory=lambda: random.choice(["D1", "D2"]))
    speaker_layout: str = "none"
    sr: int = 44100

    # reverb selection (chooses one of 1–4 as string)
    reverb_type: str = pydantic.Field(default_factory=lambda: random.choice(["1", "2", "3", "4"]))


def pad_and_normalize_audio_files(
    fg_audios: List[np.ndarray], bg_audios: List[np.ndarray]
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    def _get_rms(audio: np.ndarray) -> np.ndarray:
        # Helper function to get root mean squares of the audio
        return np.sqrt(np.mean(audio**2))

    def _add_padding(audio: np.ndarray, target_length: int) -> np.ndarray:
        # Helper function to pad an audio based on a target_length
        needed = target_length - len(audio)

        assert needed >= 0, "Unexpected target_length. Should not be smaller than audio durations."
        if needed == 0:
            return audio

        start = np.random.randint(0, needed)  # noqa: NPY002
        end = needed - start

        return np.concatenate([np.zeros(start, dtype=np.float32), audio, np.zeros(end, dtype=np.float32)])

    # RMS
    audios = fg_audios + bg_audios
    rms_list = []
    for audio in audios:
        rms_list.append(_get_rms(audio))
    rms_target = np.mean(rms_list)
    fg_audios = [audio * rms_target / _get_rms(audio) for audio in fg_audios]
    bg_audios = [audio * rms_target / _get_rms(audio) for audio in bg_audios]

    # Pad
    max_length = max([audio.shape[0] for audio in audios])
    padded_fg_audios = [_add_padding(audio, max_length) for audio in fg_audios]
    padded_bg_audios = [_add_padding(audio, max_length) for audio in bg_audios]

    return padded_fg_audios, padded_bg_audios


def validation_binaural_mix(
    trig: Path,
    control: Path,
    bg: Path,
) -> tuple[tuple[np.ndarray, np.ndarray, int], tuple[np.ndarray, None, int]]:
    """
    Mixing function specially designed for the validation experiment. Guarantees (trig, bg) (ctrl, bg) pairs with equivalent
    mixing parameters.

    Returns mixed (trig, bg), (ctrl, bg) and ground truths + sample rates for each mix.
    """
    fg_params = MixingParams()
    bg_params = MixingParams()

    # TODO: global_params
    global_params = None
    raise NotImplementedError("Need some global params")  # Should be good otherwise

    t_mix, t_gt, t_sr = binaural_mix(
        fg_list=[trig, fg_params],
        bg_list=[bg, bg_params],
        global_params=global_params,
        is_trig=True,
    )

    c_mix, c_gt, c_sr = binaural_mix(
        fg_list=[control, fg_params],
        bg_list=[bg, bg_params],
        global_params=global_params,
        is_trig=True,
    )

    return (t_mix[0], t_gt[0], t_sr), (c_mix[0], c_gt, c_sr)


def binaural_mix(
    fg_list: List[tuple[Path, MixingParams]],
    bg_list: List[tuple[Path, MixingParams]],
    global_params: MixingParams,
    *,
    is_trig: bool,
) -> tuple[List[np.ndarray], List[np.ndarray | None], int]:
    """
    Max a binaural mix of a foreground (trigger) and background sound.

    Params:
        fg_list: Paths + mixing params of foreground audio files
        bg_list : Paths + mixing params of background audio files

    Returns:
        mix : list of binaural mixed audios
        ground_truth : lust binaural ground truth audio for foreground (trigger) sound, or None if not applicable
        sr : sample rate of mixed audio
    """
    # Mixing Params
    ir_type = "BRIR"
    fg_mixing_params = [fg[1] for fg in fg_list]
    bg_mixing_params = [bg[1] for bg in bg_list]

    fg_audios = [librosa.load(fg_path, sr=global_params.sr, mono=True) for fg_path in fg_list[:,]]
    bg_audios = [librosa.load(bg_path, sr=global_params.sr, mono=True) for bg_path in bg_list[:,]]
    fg_padded, bg_padded = pad_and_normalize_audio_files(fg_audios, bg_audios)

    fg_tracks = []
    bg_tracks = []
    for params, fg_audio in zip(fg_mixing_params, fg_padded):
        fg_track = TrackObject(
            name="trigger",
            azimuth=params.azimuth,
            elevation=params.elevation,
            level=params.level,
            reverb=0.0,
            audio=fg_audio,
        )
        fg_tracks.append(fg_track)
    for params, bg_audio in zip(bg_mixing_params, bg_padded):
        bg_track = TrackObject(
            name="background",
            azimuth=params.bg_azimuth,
            elevation=params.bg_elevation,
            level=params.level,
            reverb=0.0,
            audio=bg_audio,
        )
        bg_tracks.append(bg_track)

    tracks_to_mix = fg_tracks + bg_tracks
    mix = mix_tracks_binaural(
        tracks_to_mix,
        params.subject_id,
        params.sr,
        ir_type,
        params.speaker_layout,
        mode="nearest",
        reverb_type=params.reverb_type,
    )

    if is_trig:
        ground_truth = mix_tracks_binaural(
            fg_tracks,
            params.subject_id,
            params.sr,
            ir_type,
            params.speaker_layout,
            mode="nearest",
            reverb_type=params.reverb_type,
        )
        assert ground_truth.shape == mix.shape, "Ground truth and mix shapes do not match."

        return mix, ground_truth, params.sr
    else:
        return mix, None, params.sr  # silence for control sound
