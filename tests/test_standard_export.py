from __future__ import annotations

import json

from lite_annotator.dataset_loader import DatasetType
from lite_annotator.standard_export import to_standard_task_annotation


def make_annotation(video_path: str, frames: int = 31) -> dict:
    return {
        "episode": {
            "episode_id": "episode_000000",
            "dataset_name": "Task_Name_959",
            "video_path": video_path,
            "primary_video_path": video_path,
            "views": {
                "cam_top": video_path,
                "cam_left": "/data/task/cam_left/episode_000000.mp4",
            },
            "frames": frames,
        },
        "video_text": "put banana into basket",
        "robot_setup": {
            "embodiment": "dual_arm",
            "base_mobility_type": "mobile",
            "left_effector_type": "two_finger",
            "right_effector_type": "five_finger",
        },
        "scene": {
            "task_type": "manipulation",
            "scene_location": {"space": "kitchen"},
            "objects": [
                {"name": "banana", "affordance": ["graspable"]},
                {"name": "basket", "affordance": ["receivable"]},
            ],
        },
        "subtasks": [
            {
                "start_frame": 0,
                "end_frame": 30,
                "state": "normal",
                "coordination_mode": "single_hand",
                "actions": [
                    {
                        "subject": "right_effector",
                        "skill": "pick",
                        "text": "right_effector pick up banana",
                        "slots": {
                            "manipulated_object": "banana",
                            "source_anchor": "basket",
                        },
                    }
                ],
                "phases": [
                    {
                        "target_action": "primary",
                        "start_frame": 0,
                        "end_frame": 30,
                        "action": "grasp",
                        "object": "banana",
                    }
                ],
            }
        ],
    }


def test_task_export_uses_task_level_schema_and_numeric_ids():
    bundle = {
        "task": {
            "video_text": "put banana into basket",
            "scene": make_annotation("/data/task/cam_top/episode_000000.mp4")["scene"],
            "robot_setup": make_annotation("/data/task/cam_top/episode_000000.mp4")["robot_setup"],
        },
        "annotations": {
            "episode_000000": make_annotation("/data/task/cam_top/episode_000000.mp4"),
        },
    }

    standard = to_standard_task_annotation(
        bundle,
        dataset_type=DatasetType.COROBOT,
        dataset_root="/data/task",
        primary_video_paths={"episode_000000": "/data/task/cam_top/episode_000000.mp4"},
    )

    assert standard["version"] == "annotation_schema_v1"
    assert standard["annotation_spec_version"] == "skill_spec_v1"
    assert standard["data_type"] == "corobot"
    assert standard["data_path"] == "/data/task"
    assert standard["cameras"] == [
        {"id": 0, "name": "cam_top", "role": "primary"},
        {"id": 1, "name": "cam_left", "role": "secondary"},
    ]
    assert standard["robot_setup"]["manipulators"] == [
        {"id": 0, "mount_position": "left", "end_effector_type": "two_finger"},
        {"id": 1, "mount_position": "right", "end_effector_type": "five_finger"},
    ]
    assert standard["scene"]["objects"] == [
        {"id": 0, "name": "banana", "affordance": ["graspable"]},
        {"id": 1, "name": "basket", "affordance": ["receivable"]},
    ]
    episode = standard["episode_annotation"][0]
    assert episode["id"] == 0
    assert episode["episode_video_path"] == "/data/task/cam_top/episode_000000.mp4"
    assert episode["subtasks"][0]["id"] == 0
    assert episode["subtasks"][0]["primary_action"]["phases"][0]["id"] == 0


def test_task_export_preserves_existing_automatic_episodes_by_video_path():
    bundle = {
        "task": {
            "video_text": "put banana into basket",
            "scene": make_annotation("/data/task/cam_top/episode_000000.mp4")["scene"],
            "robot_setup": make_annotation("/data/task/cam_top/episode_000000.mp4")["robot_setup"],
        },
        "annotations": {
            "episode_000000": make_annotation("/data/task/cam_top/episode_000000.mp4"),
        },
    }
    existing_standard = {
        "version": "annotation_schema_v1",
        "episode_annotation": [
            {
                "id": 0,
                "episode_video_path": "/data/task/cam_top/episode_000001.mp4",
                "frame_count": 20,
                "annotation_meta": {"source": "automatic"},
                "subtasks": [
                    {
                        "id": 0,
                        "start_frame": 0,
                        "end_frame": 19,
                        "state": "normal",
                        "coordination_mode": "single_hand",
                        "description": "auto",
                        "primary_action": {
                            "subject": "right_effector",
                            "skill": "custom",
                            "text": "auto",
                            "slots": {},
                            "phases": [],
                        },
                    }
                ],
            }
        ],
    }

    standard = to_standard_task_annotation(
        bundle,
        dataset_type=DatasetType.COROBOT,
        dataset_root="/data/task",
        primary_video_paths={"episode_000000": "/data/task/cam_top/episode_000000.mp4"},
        existing_standard=existing_standard,
    )

    assert [item["id"] for item in standard["episode_annotation"]] == [0, 1]
    assert [
        item["episode_video_path"] for item in standard["episode_annotation"]
    ] == [
        "/data/task/cam_top/episode_000000.mp4",
        "/data/task/cam_top/episode_000001.mp4",
    ]
    assert standard["episode_annotation"][1]["annotation_meta"]["source"] == "automatic"


def test_task_export_reads_common_record_from_meta_and_ignores_empty_annotations(tmp_path):
    dataset_root = tmp_path / "Task_Name_959"
    episode_root = dataset_root / "Task_Name_959_92715"
    meta_dir = episode_root / "meta"
    meta_dir.mkdir(parents=True)
    (meta_dir / "common_record.json").write_text(
        json.dumps(
            {
                "task_id": "959",
                "task_name": "Task Name",
                "machine_id": "machine_0",
            }
        ),
        encoding="utf-8",
    )
    video_path = episode_root / "videos/chunk-000/cam_top/episode_000000.mp4"
    bundle = {
        "task": {
            "video_text": "put banana into basket",
            "scene": make_annotation(str(video_path))["scene"],
            "robot_setup": make_annotation(str(video_path))["robot_setup"],
        },
        "annotations": {
            "annotated": make_annotation(str(video_path)),
            "opened_but_empty": {
                **make_annotation(str(video_path).replace("92715", "92716")),
                "subtasks": [],
            },
        },
    }

    standard = to_standard_task_annotation(
        bundle,
        dataset_type=DatasetType.COROBOT,
        dataset_root=dataset_root,
        primary_video_paths={"annotated": video_path},
        episode_order=["annotated", "opened_but_empty"],
    )

    assert standard["task_id"] == "959"
    assert standard["task_name"] == "Task Name"
    assert "machine_id" not in standard
    assert standard["data_path"] == str(dataset_root)
    assert len(standard["episode_annotation"]) == 1
    assert standard["episode_annotation"][0]["episode_video_path"] == str(video_path)
