from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lite_annotator.annotation_store import default_annotation_dir
from lite_annotator.dataset_loader import DatasetType

STANDARD_VERSION = "robolabletools_v1"


def standard_annotation_path(dataset_root: str | Path, annotation_stem: str) -> Path:
    return default_annotation_dir(dataset_root) / f"{annotation_stem}_standard.json"


def normalized_data_type(dataset_type) -> str:
    value = str(getattr(dataset_type, "value", dataset_type) or "")
    if value == DatasetType.LEROBOT.value:
        return "lerobot"
    if value == DatasetType.COROBOT.value:
        return "corobot"
    return value or "unknown"


def parse_episode_index(episode_id: str) -> int:
    matches = re.findall(r"(\d+)", str(episode_id or ""))
    return int(matches[-1]) if matches else 0


def standard_scene(scene: dict[str, Any] | None) -> dict[str, Any]:
    scene = scene if isinstance(scene, dict) else {}
    objects = []
    for obj in scene.get("objects") or []:
        if not isinstance(obj, dict):
            continue
        name = str(obj.get("name", "")).strip()
        if not name:
            continue
        objects.append({
            "name": name,
            "affordance": list(obj.get("affordance") or []),
        })
    return {
        "scene_level": "room",
        "objects": objects,
    }


def standard_phase_list(phases, subject: str) -> list[dict[str, Any]]:
    result = []
    for phase in phases or []:
        if not isinstance(phase, dict):
            continue
        result.append({
            "start_frame": int(phase.get("start_frame", 0)),
            "end_frame": int(phase.get("end_frame", 0)),
            "action": str(phase.get("action", "")),
            "subject": subject,
        })
    return result


def standard_action(action: dict[str, Any], phases) -> dict[str, Any]:
    subject = str(action.get("subject", ""))
    return {
        "subject": subject,
        "skill": str(action.get("skill", "")),
        "text": str(action.get("text", "")),
        "slots": dict(action.get("slots") or {}),
        "phase": standard_phase_list(phases, subject),
    }


def subtask_description(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return ""
    primary_text = str(actions[0].get("text", ""))
    if len(actions) == 1:
        return primary_text
    auxiliary_text = str(actions[1].get("text", ""))
    return f"{primary_text}, while {auxiliary_text} to assist/support the primary action"


def standard_subtask(subtask: dict[str, Any], slot_index: int) -> dict[str, Any]:
    actions = [
        action for action in (subtask.get("actions") or [])
        if isinstance(action, dict)
    ]
    phases = subtask.get("phases") or []
    result = {
        "slot_index": slot_index,
        "start_frame": int(subtask.get("start_frame", 0)),
        "end_frame": int(subtask.get("end_frame", 0)),
        "coordination_mode": str(subtask.get("coordination_mode", "")),
        "description": subtask_description(actions),
        "primary_action": standard_action(actions[0], phases) if actions else None,
    }
    if len(actions) > 1:
        result["auxiliary_action"] = standard_action(actions[1], phases)
    return result


def to_standard_annotation(
    annotation: dict[str, Any],
    dataset_type=DatasetType.UNKNOWN,
    data_path: str | Path | None = None,
) -> dict[str, Any]:
    episode = annotation.get("episode") or {}
    scene = annotation.get("scene") or {}
    subtasks = [
        standard_subtask(subtask, index)
        for index, subtask in enumerate(annotation.get("subtasks") or [], start=1)
        if isinstance(subtask, dict)
    ]
    return {
        "version": STANDARD_VERSION,
        "task_id": str(episode.get("task_id", "")),
        "task_type": str(scene.get("task_type", "")),
        "episode_index": parse_episode_index(str(episode.get("episode_id", ""))),
        "frame_count": int(episode.get("frames", 0)),
        "data_type": normalized_data_type(dataset_type),
        "data_path": str(data_path or episode.get("primary_video_path") or episode.get("video_path") or ""),
        "task_description": str(annotation.get("video_text", "")),
        "robot_setup": dict(annotation.get("robot_setup") or {}),
        "scene": standard_scene(scene),
        "subtasks": subtasks,
    }
