"""Aggregate quality score across the full video pipeline."""

from __future__ import annotations

from typing import Any

from app.services.video_engine.models import PipelineStage, QualityScore


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    if score >= 0.8:
        return "B"
    if score >= 0.7:
        return "C"
    if score >= 0.55:
        return "D"
    return "F"


def build_quality_score(
    stages: list[PipelineStage],
    *,
    cinematic_quality: dict[str, Any] | None = None,
    character_consistency: dict[str, Any] | None = None,
    production_render: dict[str, Any] | None = None,
    scene_render: dict[str, Any] | None = None,
) -> QualityScore:
    by_name = {s.name: s for s in stages}

    def stage_score(name: str, default: float = 0.4) -> float:
        s = by_name.get(name)
        return _clamp(s.score if s else default)

    cq = cinematic_quality or {}
    overall_cinematic = cq.get("overall")
    try:
        cinematic = _clamp(float(overall_cinematic)) if overall_cinematic is not None else 0.7
    except (TypeError, ValueError):
        cinematic = 0.7

    cc = character_consistency or {}
    cons = cc.get("consistency_score") or {}
    if isinstance(cons, dict):
        try:
            consistency = _clamp(float(cons.get("overall", 0.7)))
        except (TypeError, ValueError):
            consistency = 0.7
    else:
        try:
            consistency = _clamp(float(cons)) if cons else 0.7
        except (TypeError, ValueError):
            consistency = 0.7

    export_ok = bool(((production_render or {}).get("validation") or {}).get("passed"))
    export_score = 0.95 if export_ok else stage_score("export", 0.45)
    render_score = stage_score("rendering")
    if (scene_render or {}).get("ray_tracing_ready"):
        render_score = _clamp(render_score + 0.05)

    prompt = stage_score("prompt")
    director = stage_score("director")
    scene = stage_score("scene")
    shot = stage_score("shot")
    camera = stage_score("camera")
    generation = stage_score("generation")

    weights = {
        "prompt": 0.08,
        "director": 0.10,
        "scene": 0.12,
        "shot": 0.10,
        "camera": 0.10,
        "generation": 0.12,
        "rendering": 0.12,
        "export": 0.12,
        "consistency": 0.08,
        "cinematic": 0.06,
    }
    parts = {
        "prompt": prompt,
        "director": director,
        "scene": scene,
        "shot": shot,
        "camera": camera,
        "generation": generation,
        "rendering": render_score,
        "export": export_score,
        "consistency": consistency,
        "cinematic": cinematic,
    }
    overall = sum(parts[k] * weights[k] for k in weights)
    overall = _clamp(round(overall, 3))
    production_ready = (
        overall >= 0.75
        and export_ok
        and all(
            by_name.get(n) and by_name[n].status in ("passed", "recovered", "pending")
            for n in ("prompt", "director", "scene", "shot", "camera")
        )
        and by_name.get("prompt") is not None
        and by_name["prompt"].status == "passed"
    )

    return QualityScore(
        overall=overall,
        prompt=prompt,
        director=director,
        scene=scene,
        shot=shot,
        camera=camera,
        generation=generation,
        rendering=render_score,
        export=export_score,
        consistency=consistency,
        production_ready=production_ready,
        grade=_grade(overall),
        breakdown=parts,
    )
