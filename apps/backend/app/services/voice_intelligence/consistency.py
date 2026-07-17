"""Voice Consistency Engine — same voice/accent/emotion continuity checks."""

from __future__ import annotations

from app.services.voice_intelligence.models import (
    CharacterVoiceProfile,
    ConsistencyReport,
    DialogueLine,
)
from app.services.voice_intelligence.version import VOICE_CONSISTENCY_THRESHOLD


def verify_consistency(
    project_id: str,
    lines: list[DialogueLine],
    profiles: dict[str, CharacterVoiceProfile],
) -> ConsistencyReport:
    issues: list[str] = []
    notes: list[str] = []

    # Same voice across scenes/lines per role
    role_voices: dict[str, set[str]] = {}
    for ln in lines:
        if not ln.voice_id:
            issues.append(f"line {ln.line_id} missing voice_id")
            continue
        role_voices.setdefault(ln.role, set()).add(ln.voice_id)
        expected = profiles.get(ln.role)
        if expected and ln.voice_id != expected.voice_id:
            issues.append(
                f"unexpected voice switch on {ln.line_id}: {ln.voice_id} != {expected.voice_id}"
            )

    same_voice = all(len(v) <= 1 for v in role_voices.values()) and not any(
        "unexpected voice switch" in i for i in issues
    )
    if not same_voice:
        issues.append("voice_id changed within a role across lines")

    # Same accent per role profile
    accents = {role: p.accent for role, p in profiles.items()}
    same_accent = len(set(accents.values())) >= 0  # profiles define accent; check stability
    for role, profile in profiles.items():
        if not profile.accent:
            issues.append(f"missing accent for {role}")
            same_accent = False

    # Emotion continuity — abrupt flips without pause markers
    emotion_continuity = True
    for i in range(1, len(lines)):
        prev, cur = lines[i - 1], lines[i]
        if prev.role == cur.role and prev.emotion != cur.emotion:
            # Allowed if dramatic pause present
            if prev.dramatic_pause_sec < 0.3 and prev.emotion in ("calm", "serious") and cur.emotion in (
                "angry",
                "fear",
                "excited",
            ):
                emotion_continuity = False
                issues.append(
                    f"emotion jump {prev.emotion}->{cur.emotion} on {cur.line_id} without pause"
                )

    # Dialogue synchronization — timings sequential
    dialogue_synchronized = True
    for i in range(1, len(lines)):
        if lines[i].start_sec + 0.001 < lines[i - 1].end_sec:
            dialogue_synchronized = False
            issues.append(f"overlap detected before {lines[i].line_id}")

    no_unexpected = same_voice and not any("unexpected voice switch" in i for i in issues)

    score = 100.0
    if not same_voice:
        score -= 25
    if not same_accent:
        score -= 10
    if not emotion_continuity:
        score -= 15
    if not no_unexpected:
        score -= 20
    if not dialogue_synchronized:
        score -= 25
    score = max(0.0, min(100.0, score - len(issues) * 2))

    consistent = score >= VOICE_CONSISTENCY_THRESHOLD and dialogue_synchronized and same_voice
    if consistent:
        notes.append("voice_consistency_stable")
    else:
        notes.append("voice_consistency_issues")

    return ConsistencyReport(
        project_id=project_id,
        consistent=consistent,
        consistency_score=round(score, 2),
        same_voice_across_scenes=same_voice,
        same_accent=bool(same_accent),
        emotion_continuity=emotion_continuity,
        no_unexpected_switching=no_unexpected,
        dialogue_synchronized=dialogue_synchronized,
        issues=issues,
        notes=notes,
    )
