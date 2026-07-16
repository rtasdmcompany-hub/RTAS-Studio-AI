"""Build rich IdentityProfiles from Character Memory + Prompt Understanding."""

from __future__ import annotations

from app.services.intelligence.character_consistency.embeddings import build_face_embedding
from app.services.intelligence.character_consistency.models import (
    IdentityProfile,
    SubjectKind,
)
from app.services.intelligence.character_consistency.subject_detector import (
    detect_subject_kind,
    expected_track_count,
)
from app.services.intelligence.director_models import CharacterMemory


def _voice_for(gender: str, age: str) -> str:
    if age in ("child", "teen"):
        return "youthful clear voice"
    if gender == "female":
        return "warm mid female narration tone"
    if gender == "male":
        return "grounded mid male narration tone"
    return "neutral cinematic voice"


def _walk_for(emotion_hint: str, age: str) -> str:
    e = (emotion_hint or "").lower()
    if "sad" in e or "lonely" in e or "somber" in e:
        return "slow heavy gait, shoulders slightly forward"
    if "action" in e or "fear" in e:
        return "urgent purposeful stride"
    if age == "elder":
        return "careful measured walk"
    return "natural steady walk"


def _pose_for(kind: SubjectKind, index: int) -> str:
    if kind == "vehicle":
        return "hero three-quarter product stance"
    if kind == "animal":
        return "natural standing / alert animal pose"
    if kind == "crowd":
        return "group mid-ground natural stance"
    if index == 0:
        return "medium standing / walking three-quarter"
    return "supporting character open stance"


def _expression_for(emotion_hint: str) -> str:
    e = (emotion_hint or "").lower()
    mapping = {
        "sad": "soft sorrow, downcast eyes",
        "somber": "soft sorrow, downcast eyes",
        "lonely": "distant restrained gaze",
        "joy": "open warm smile",
        "joyful": "open warm smile",
        "fear": "tense wide eyes",
        "dramatic": "intense focused expression",
        "calm": "relaxed neutral face",
        "romance": "tender soft smile",
    }
    for key, val in mapping.items():
        if key in e:
            return val
    return "natural cinematic expression"


def _lighting_adaptation(understanding: dict | None) -> str:
    understanding = understanding or {}
    time = str(understanding.get("time") or "Day")
    weather = str(understanding.get("weather") or "Clear")
    lighting = understanding.get("lighting") or []
    if isinstance(lighting, list):
        light_txt = ", ".join(str(x) for x in lighting[:3])
    else:
        light_txt = str(lighting)
    return (
        f"Preserve identity under {time.lower()} / {weather.lower()} lighting "
        f"({light_txt or 'natural'}); skin and eye color must not shift with grade."
    )


def _body_for(kind: SubjectKind, age: str, gender: str) -> str:
    if kind == "vehicle":
        return "vehicle body proportions locked (make/model silhouette)"
    if kind == "animal":
        return "animal anatomy locked (species-accurate proportions)"
    if age == "child":
        return "child proportions, smaller frame"
    if age == "elder":
        return "adult elder proportions"
    if gender == "female":
        return "adult female proportions, consistent height"
    if gender == "male":
        return "adult male proportions, consistent height"
    return "consistent human proportions"


def build_identity_profiles(
    *,
    prompt: str,
    characters: list[CharacterMemory],
    understanding: dict | None = None,
    emotion_hint: str | None = None,
) -> tuple[SubjectKind, list[IdentityProfile]]:
    kind = detect_subject_kind(prompt, character_count=len(characters) or 1)
    target = expected_track_count(kind, len(characters) or 1)
    memories = list(characters)

    # Pad / trim track list for cast type without inventing contradictory identities.
    while len(memories) < target and memories:
        base = memories[len(memories) % len(characters)] if characters else None
        if base is None:
            break
        clone_id = f"{base.character_id}_T{len(memories)}"
        memories.append(
            CharacterMemory(
                character_id=clone_id,
                gender=base.gender,
                age=base.age,
                hair=base.hair,
                beard=base.beard,
                skin_tone=base.skin_tone,
                face_shape=base.face_shape,
                eye_color=base.eye_color,
                outfit=base.outfit,
                accessories=list(base.accessories),
                reference_image_urls=list(base.reference_image_urls),
                face_embedding_ref=base.face_embedding_ref,
                locked_traits=list(base.locked_traits),
            )
        )
    memories = memories[:target] or memories

    emotion = emotion_hint or ""
    if understanding and isinstance(understanding.get("emotion"), list):
        emotion = emotion or ", ".join(str(x) for x in understanding["emotion"][:2])
    elif understanding and understanding.get("mood"):
        emotion = emotion or str(understanding.get("mood"))

    profiles: list[IdentityProfile] = []
    for i, mem in enumerate(memories):
        if kind == "vehicle" and i == 0:
            identity = "hero vehicle identity"
            face = "grille / front fascia identity"
            hair = "n/a"
            clothes = "paint and trim locked"
            voice = "engine character / ambience"
            walk = "vehicle motion language locked"
        elif kind == "animal" and i == 0:
            identity = "hero animal identity"
            face = "species face markings locked"
            hair = "fur / coat pattern locked"
            clothes = "n/a"
            voice = "species-accurate vocalization bed"
            walk = "species gait locked"
        else:
            identity = f"{mem.gender} {mem.age} lead" if i == 0 else f"{mem.gender} {mem.age} support"
            face = f"{mem.face_shape} face, unique likeness"
            hair = mem.hair
            clothes = mem.outfit
            voice = _voice_for(mem.gender, mem.age)
            walk = _walk_for(emotion, mem.age)

        traits_fp = (
            f"{hair}|{mem.age}|{mem.skin_tone}|{mem.eye_color}|{clothes}"
        )
        embedding, emb_ref = build_face_embedding(
            subject_id=mem.character_id,
            reference_image_urls=mem.reference_image_urls,
            traits_fingerprint=traits_fp,
        )

        locked = [
            "identity",
            "face",
            "hair",
            "age",
            "body",
            "clothes",
            "accessories",
            "skin_tone",
            "eye_color",
            "walking_style",
            "voice",
        ]

        profiles.append(
            IdentityProfile(
                subject_id=mem.character_id,
                subject_kind=kind if kind in ("animal", "vehicle", "crowd", "family") else (
                    "two_characters" if kind == "two_characters" else "single_character"
                ),
                identity=identity,
                face=face,
                hair=hair,
                age=mem.age,
                body=_body_for(kind, mem.age, mem.gender),
                clothes=clothes,
                accessories=list(mem.accessories),
                pose=_pose_for(kind, i),
                expression=_expression_for(emotion),
                voice=voice,
                walking_style=walk,
                skin_tone=mem.skin_tone,
                eye_color=mem.eye_color,
                lighting_adaptation=_lighting_adaptation(understanding),
                face_embedding=embedding,
                face_embedding_ref=emb_ref,
                reference_image_urls=list(mem.reference_image_urls),
                locked_traits=locked,
            )
        )

    return kind, profiles
