"""Mix profile builders — ducking, EQ, compression, routing."""

from __future__ import annotations

from typing import Any

from app.services.mixing_mastering.models import ChannelGains, MixProfile


def build_mix_profile(
    *,
    dialogue_priority: bool = True,
    music_ducking_db: float | None = None,
    sfx_balance: float | None = None,
    ambient_level: float | None = None,
    voice_summary: dict[str, Any] | None = None,
    music_summary: dict[str, Any] | None = None,
    sfx_summary: dict[str, Any] | None = None,
) -> MixProfile:
    duck = -8.0 if music_ducking_db is None else float(music_ducking_db)
    sfx = 0.75 if sfx_balance is None else float(sfx_balance)
    amb = 0.45 if ambient_level is None else float(ambient_level)

    voice_gain = 1.0
    music_gain = 0.55 if dialogue_priority else 0.7
    # Hotter music energy → more ducking
    if music_summary:
        energy = float(music_summary.get("energy") or 0.5)
        music_gain = max(0.25, music_gain - energy * 0.15)
        duck = min(duck, -6.0 - energy * 4.0)

    if voice_summary and voice_summary.get("production_ready"):
        voice_gain = 1.05

    if sfx_summary:
        layers = int(sfx_summary.get("layers") or 1)
        sfx = max(0.4, sfx - layers * 0.03)
        amb = float(sfx_summary.get("volume") or amb)

    return MixProfile(
        dialogue_priority=dialogue_priority,
        music_ducking_db=round(duck, 2),
        sfx_balance=round(sfx, 3),
        ambient_level=round(amb, 3),
        stereo_pan_voice=0.0,
        stereo_pan_music=0.0,
        compression_ratio=3.0 if dialogue_priority else 2.5,
        limiter_ceiling_db=-1.0,
        eq_low_gain_db=-0.5,
        eq_mid_gain_db=1.5 if dialogue_priority else 0.5,
        eq_high_gain_db=0.5,
        gains=ChannelGains(
            voice=round(voice_gain, 3),
            music=round(music_gain, 3),
            sfx=round(sfx, 3),
            ambient=round(amb, 3),
        ),
    )


def describe_mix_chain(profile: MixProfile) -> list[str]:
    return [
        "channel_routing:voice>music>sfx>ambient",
        f"dialogue_priority:{profile.dialogue_priority}",
        f"music_duck:{profile.music_ducking_db}dB",
        f"compressor:{profile.compression_ratio}:1",
        f"eq:low={profile.eq_low_gain_db}/mid={profile.eq_mid_gain_db}/high={profile.eq_high_gain_db}",
        f"limiter:{profile.limiter_ceiling_db}dB",
        f"gains:{profile.gains.to_dict()}",
    ]
