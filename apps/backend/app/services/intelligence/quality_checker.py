"""Quality Checker — validates planned package before generation queue."""

from __future__ import annotations

from app.services.intelligence.models import (
    IntelligencePipelineResult,
    QualityCheckResult,
)


def check_plan_quality(plan: IntelligencePipelineResult) -> QualityCheckResult:
    issues: list[str] = []
    recommendations: list[str] = []

    if not plan.enhancement.enhanced_prompt.strip():
        issues.append("empty_enhanced_prompt")
    if not plan.scenes:
        issues.append("no_scenes")
    if not plan.shots:
        issues.append("no_shots")

    total_scene = sum(s.duration_seconds for s in plan.scenes)
    total_shot = sum(s.duration_seconds for s in plan.shots)
    if abs(total_scene - total_shot) > 2:
        issues.append("duration_mismatch")
        recommendations.append("Align shot durations to scene durations")

    if plan.intelligence.missing_information:
        recommendations.append(
            "Optional: supply " + ", ".join(plan.intelligence.missing_information[:3])
        )

    score = 1.0
    score -= 0.2 * len(issues)
    score -= 0.05 * len(plan.intelligence.missing_information)
    score = max(0.0, min(1.0, score))

    return QualityCheckResult(
        passed=len(issues) == 0,
        score=round(score, 2),
        issues=issues,
        recommendations=recommendations,
    )
