"""Audio layering, spatial metadata, timeline sync."""

from __future__ import annotations

from app.services.sfx_ambient.categories import get_category
from app.services.sfx_ambient.models import AudioLayer, SpatialMeta, TimelineEvent


def build_layers(
    categories: list[str],
    *,
    duration_sec: float,
    base_volume: float,
    loop: bool,
    fade_in_sec: float,
    fade_out_sec: float,
    job_id: str,
) -> list[AudioLayer]:
    layers: list[AudioLayer] = []
    n = max(1, len(categories))
    for i, cat in enumerate(categories):
        cdef = get_category(cat)
        # Distance / pan simulation across layers
        distance = min(1.0, 0.2 + i * 0.15)
        pan = -0.6 + (1.2 * i / max(n - 1, 1)) if n > 1 else 0.0
        vol = round(min(1.0, base_volume * cdef.default_volume / 0.5), 3)
        # Dynamic ducking: later layers slightly quieter
        vol = round(vol * (1.0 - i * 0.08), 3)
        layer_id = f"layer_{job_id}_{i}"
        layers.append(
            AudioLayer(
                layer_id=layer_id,
                category=cat,
                kind=cdef.kind if cdef.kind != "both" else "ambient",
                volume=max(0.05, vol),
                start_sec=0.0,
                end_sec=duration_sec,
                loop=loop if cdef.loopable else False,
                fade_in_sec=fade_in_sec,
                fade_out_sec=fade_out_sec,
                spatial=SpatialMeta(
                    x=round(pan, 3),
                    y=0.0,
                    z=round(distance, 3),
                    distance=round(distance, 3),
                    pan=round(pan, 3),
                ),
                asset_url=f"/media/sfx/{job_id}/{cat}.wav",
                library_id=f"sfxlib_{job_id}_{i}",
            )
        )
    return layers


def build_timeline_events(
    layers: list[AudioLayer],
    *,
    scene_id: str | None,
    job_id: str,
) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for i, layer in enumerate(layers):
        events.append(
            TimelineEvent(
                event_id=f"evt_{job_id}_{i}_play",
                scene_id=scene_id,
                at_sec=layer.start_sec,
                category=layer.category,
                action="play",
                layer_id=layer.layer_id,
                metadata={"volume": layer.volume, "loop": layer.loop},
            )
        )
        if layer.fade_out_sec > 0:
            fade_at = max(0.0, layer.end_sec - layer.fade_out_sec)
            events.append(
                TimelineEvent(
                    event_id=f"evt_{job_id}_{i}_fade",
                    scene_id=scene_id,
                    at_sec=fade_at,
                    category=layer.category,
                    action="fade",
                    layer_id=layer.layer_id,
                    metadata={"fade_out_sec": layer.fade_out_sec},
                )
            )
    events.sort(key=lambda e: e.at_sec)
    return events
