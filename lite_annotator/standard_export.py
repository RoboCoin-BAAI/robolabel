from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lite_annotator.annotation_store import default_annotation_dir
from lite_annotator.dataset_loader import DatasetType

STANDARD_VERSION = "v2"
ANNOTATION_SPEC_VERSION = "skill_spec_v1"


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


def split_task_from_dataset_name(dataset_name: str) -> tuple[str, str]:
    text = str(dataset_name or "")
    match = re.match(r"(.+)_([0-9]+)$", text)
    if not match:
        return text, ""
    return match.group(1), match.group(2)


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def lerobot_root_from_episode(episode: dict[str, Any], fallback: str | Path | None = None) -> Path | None:
    video_path = Path(str(episode.get("primary_video_path") or episode.get("video_path") or ""))
    if video_path:
        for parent in video_path.parents:
            if (parent / "meta" / "info.json").exists():
                return parent
    if fallback:
        fallback_path = Path(fallback)
        if (fallback_path / "meta" / "info.json").exists():
            return fallback_path
    return None


def candidate_metadata_roots(episode: dict[str, Any], dataset_root: str | Path | None) -> list[Path]:
    roots = []
    lerobot_root = lerobot_root_from_episode(episode, dataset_root)
    if lerobot_root:
        roots.append(lerobot_root)
        roots.append(lerobot_root.parent)
    if dataset_root:
        roots.append(Path(dataset_root))
    unique = []
    for root in roots:
        if root and root not in unique:
            unique.append(root)
    return unique


def read_common_record(episode: dict[str, Any], dataset_root: str | Path | None) -> dict[str, Any]:
    for root in candidate_metadata_roots(episode, dataset_root):
        data = read_json_file(root / "common_record.json")
        if data:
            return data
    return {}


def read_op_dataid(episode: dict[str, Any], dataset_root: str | Path | None) -> str | None:
    episode_index = parse_episode_index(str(episode.get("episode_id", "")))
    for root in candidate_metadata_roots(episode, dataset_root):
        path = root / "op_dataid.jsonl"
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if int(item.get("episode_index", -1)) == episode_index:
                        dataid = str(item.get("dataid", "")).strip()
                        if dataid:
                            return dataid
        except OSError:
            continue
    return None


def standard_cameras(episode: dict[str, Any], primary_video_path: str) -> dict[str, dict[str, str]]:
    views = episode.get("views") if isinstance(episode.get("views"), dict) else {}
    cameras = {}
    for camera, path in views.items():
        role = "primary" if str(path) == str(primary_video_path) else "secondary"
        cameras[str(camera)] = {"role": role}
    return cameras


def standard_scene(scene: dict[str, Any] | None) -> dict[str, Any]:
    scene = scene if isinstance(scene, dict) else {}
    location = scene.get("scene_location") if isinstance(scene.get("scene_location"), dict) else {}
    objects = []
    for index, obj in enumerate(scene.get("objects") or []):
        if not isinstance(obj, dict):
            continue
        name = str(obj.get("name", "")).strip()
        if not name:
            continue
        objects.append({
            "object_id": f"obj_{index}",
            "name": name,
            "affordance": list(obj.get("affordance") or []),
        })
    return {
        "scene_type": str(location.get("space") or scene.get("task_type", "")),
        "objects": objects,
    }


def standard_robot_setup(robot_setup: dict[str, Any] | None) -> dict[str, Any]:
    robot_setup = robot_setup if isinstance(robot_setup, dict) else {}
    embodiment = str(robot_setup.get("embodiment", "dual_arm"))
    base_mobility = str(robot_setup.get("base_mobility_type", "unknown") or "unknown")
    manipulators = []
    if embodiment == "single_arm":
        manipulators.append({
            "manipulator_id": "arm_0",
            "mount_position": "center",
            "end_effector": {
                "type": str(robot_setup.get("single_effector_type", "two_finger")),
            },
        })
    else:
        manipulators.extend([
            {
                "manipulator_id": "arm_0",
                "mount_position": "left",
                "end_effector": {
                    "type": str(robot_setup.get("left_effector_type", "two_finger")),
                },
            },
            {
                "manipulator_id": "arm_1",
                "mount_position": "right",
                "end_effector": {
                    "type": str(robot_setup.get("right_effector_type", "two_finger")),
                },
            },
        ])
    return {
        "base": {
            "mobility_type": base_mobility,
        },
        "manipulators": manipulators,
    }


def standard_phase_list(phases, target_action: str) -> list[dict[str, Any]]:
    result = []
    for phase in phases or []:
        if not isinstance(phase, dict):
            continue
        if str(phase.get("target_action", "primary") or "primary") != target_action:
            continue
        result.append({
            "phase_index": len(result) + 1,
            "start_frame": int(phase.get("start_frame", 0)),
            "end_frame": int(phase.get("end_frame", 0)),
            "action": str(phase.get("action", "")),
            "object": str(phase.get("object", "")),
        })
    return result


def standard_action(action: dict[str, Any], phases, target_action: str) -> dict[str, Any]:
    return {
        "subject": str(action.get("subject", "")),
        "skill": str(action.get("skill", "")),
        "text": str(action.get("text", "")),
        "slots": dict(action.get("slots") or {}),
        "phases": standard_phase_list(phases, target_action),
    }


def subtask_description(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return ""
    primary_text = str(actions[0].get("text", ""))
    if len(actions) == 1:
        return primary_text
    auxiliary_text = str(actions[1].get("text", ""))
    return f"{primary_text}, while {auxiliary_text} to assist/support the primary action"


def standard_subtask(subtask: dict[str, Any], subtask_index: int) -> dict[str, Any]:
    actions = [
        action for action in (subtask.get("actions") or [])
        if isinstance(action, dict)
    ]
    phases = subtask.get("phases") or []
    result = {
        "subtask_index": subtask_index,
        "start_frame": int(subtask.get("start_frame", 0)),
        "end_frame": int(subtask.get("end_frame", 0)),
        "state": str(subtask.get("state", "normal") or "normal"),
        "coordination_mode": str(subtask.get("coordination_mode", "")),
        "description": subtask_description(actions),
        "primary_action": standard_action(actions[0], phases, "primary") if actions else None,
    }
    if len(actions) > 1:
        result["auxiliary_action"] = standard_action(actions[1], phases, "auxiliary")
    return result


def to_standard_annotation(
    annotation: dict[str, Any],
    dataset_type=DatasetType.UNKNOWN,
    data_path: str | Path | None = None,
    dataset_root: str | Path | None = None,
) -> dict[str, Any]:
    episode = annotation.get("episode") or {}
    scene = annotation.get("scene") or {}
    common_record = read_common_record(episode, dataset_root)
    op_dataid = read_op_dataid(episode, dataset_root)
    primary_video_path = str(data_path or episode.get("primary_video_path") or episode.get("video_path") or "")
    fallback_task_name, fallback_task_id = split_task_from_dataset_name(
        str(episode.get("dataset_name", ""))
    )
    subtasks = [
        standard_subtask(subtask, index)
        for index, subtask in enumerate(annotation.get("subtasks") or [])
        if isinstance(subtask, dict)
    ]
    task_id = str(common_record.get("task_id") or fallback_task_id or episode.get("task_id", ""))
    result = {
        "version": STANDARD_VERSION,
        "annotation_spec_version": ANNOTATION_SPEC_VERSION,
        "task_name": str(common_record.get("task_name") or fallback_task_name or episode.get("task_id", "")),
        "task_id": task_id,
        "task_type": str(scene.get("task_type", "")),
        "episode_index": op_dataid or parse_episode_index(str(episode.get("episode_id", ""))),
        "frame_count": int(episode.get("frames", 0)),
        "data_type": normalized_data_type(dataset_type),
        "data_path": primary_video_path,
        "cameras": standard_cameras(episode, primary_video_path),
        "task_description": str(annotation.get("video_text", "")),
        "annotation_meta": {
            "source": "human",
        },
        "robot_setup": standard_robot_setup(annotation.get("robot_setup")),
        "scene": standard_scene(scene),
        "subtasks": subtasks,
    }
    machine_id = str(common_record.get("machine_id", "")).strip()
    if machine_id:
        result["machine_id"] = machine_id
    return result
