from collections.abc import Collection

import librosa
import numpy as np

from ._binamix import custom_mix_tracks_binaural, setup_binamix
from .interface import GlobalMixingParams, SourceDataItem, SourceTrack

setup_binamix()
from binamix.sadie_utilities import TrackObject  # type: ignore  # noqa: I001


TrackAudioSpec = tuple[SourceTrack, np.ndarray]


def prepare_track_specs(
    fg_items: Collection[SourceDataItem],
    bg_items: Collection[SourceDataItem],
    global_params: GlobalMixingParams,
    *,
    fg_track_options: dict | None = None,
    bg_track_options: dict | None = None,
    rng: np.random.Generator | None = None,
) -> tuple[tuple[TrackAudioSpec, ...], tuple[TrackAudioSpec, ...]]:
    if rng is None:
        rng = np.random.default_rng()

    def _load_audios(item: SourceDataItem) -> tuple[SourceDataItem, np.ndarray]:
        return item, librosa.load(item.file_path, sr=global_params.sample_rate, mono=True)[0]

    def _normalize_audios(
        fg_audios: tuple[SourceDataItem, np.ndarray], bg_audios: tuple[SourceDataItem, np.ndarray]
    ) -> tuple[tuple[SourceDataItem, np.ndarray], tuple[SourceDataItem, np.ndarray]]:
        rms_fg = [np.sqrt(np.mean(audio**2)) for _, audio in fg_audios]
        rms_bg = [np.sqrt(np.mean(audio**2)) for _, audio in bg_audios]

        rms_target = np.mean(rms_fg + rms_bg)

        fg_norm = tuple(
            (item, audio * (rms_target / rms)) if rms > 1e-6 else (item, audio)
            for (item, audio), rms in zip(fg_audios, rms_fg)
        )
        bg_norm = tuple(
            (item, audio * (rms_target / rms)) if rms > 1e-6 else (item, audio)
            for (item, audio), rms in zip(bg_audios, rms_bg)
        )

        return fg_norm, bg_norm

    def _generate_padded_track_specs(
        item: SourceDataItem, audio: np.ndarray, max_len: int, options: dict
    ) -> TrackAudioSpec:
        # Find placement at random (rest will be zero padded)
        length = audio.shape[0]
        start = rng.integers(0, max_len - length) if max_len > length else 0
        end = start + length

        track = SourceTrack(
            source_item=item,
            start=start,
            end=end,
            _rng=rng,
            **options,
        )

        padded_audio = np.pad(audio, (start, max_len - end), mode="constant")

        return track, padded_audio

    fg_audios = tuple(map(_load_audios, fg_items))
    bg_audios = tuple(map(_load_audios, bg_items))

    fg_normalized, bg_normalized = _normalize_audios(fg_audios, bg_audios)

    max_length = max(
        max(audio.shape[0] for _, audio in fg_normalized), max(audio.shape[0] for _, audio in bg_normalized)
    )
    fg_specs = tuple(
        _generate_padded_track_specs(item, audio, max_length, fg_track_options or {}) for item, audio in fg_normalized
    )
    bg_specs = tuple(
        _generate_padded_track_specs(item, audio, max_length, bg_track_options or {}) for item, audio in bg_normalized
    )

    return fg_specs, bg_specs


def binaural_mix(
    fg_tracks: tuple[TrackAudioSpec, ...],
    bg_tracks: tuple[TrackAudioSpec, ...],
    global_params: GlobalMixingParams,
    *,
    is_trig: bool,
) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Max a binaural mix of a foreground (trigger) and background sound.
    """

    def _make_binamix_track(spec: TrackAudioSpec) -> TrackObject:
        track, padded_audio = spec
        return TrackObject(
            name=track.source_item.file_path.stem,
            azimuth=track.azimuth,
            elevation=track.elevation,
            level=track.level,
            reverb=track.reverb,
            audio=padded_audio,
        )

    fg_binamix_tracks = list(map(_make_binamix_track, fg_tracks))
    bg_binamix_tracks = list(map(_make_binamix_track, bg_tracks))

    mix = custom_mix_tracks_binaural(
        tracks=[*fg_binamix_tracks, *bg_binamix_tracks],
        subject_id=global_params.subject_id,
        sample_rate=global_params.sample_rate,
        ir_type=global_params.ir_type,
        speaker_layout=global_params.speaker_layout,
        mode=global_params.mode,
        reverb_type=global_params.reverb_type,
    )

    if is_trig:
        ground_truth = custom_mix_tracks_binaural(
            tracks=fg_binamix_tracks,
            subject_id=global_params.subject_id,
            sample_rate=global_params.sample_rate,
            ir_type=global_params.ir_type,
            speaker_layout=global_params.speaker_layout,
            mode=global_params.mode,
            reverb_type=global_params.reverb_type,
        )
        assert ground_truth.shape == mix.shape, "Ground truth and mix shapes do not match."

        return mix, ground_truth
    else:
        return mix, None  # silence for control sound


# def validation_binaural_mix(
#     trig: Path,
#     control: Path,
#     bg: Path,
# ) -> tuple[tuple[np.ndarray, np.ndarray, int], tuple[np.ndarray, np.ndarray, int]]:
#     """
#     Mixing function specially designed for the validation experiment. Guarantees (trig, bg) (ctrl, bg) pairs with equivalent
#     mixing parameters.

#     Returns mixed (trig, bg), (ctrl, bg) and ground truths + sample rates for each mix.
#     """
#     raise NotImplementedError("This function is not implemented yet.")
#     # params = MixingParams()

#     # t_mix, t_gt, t_sr = binaural_mix(
#     #     trig,
#     #     bg,
#     #     params,
#     #     is_trig=True,
#     # )

#     # c_mix, c_gt, c_sr = binaural_mix(
#     #     trig,
#     #     bg,
#     #     params,
#     #     is_trig=False,
#     # )

#     # raise NotImplementedError("Control variable is not even used here ...")

#     # return (t_mix, t_gt, t_sr), (c_mix, c_gt, c_sr)
