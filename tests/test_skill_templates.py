from __future__ import annotations

from common.skill_schema import load_skill_templates


def test_anchor_slots_allow_effector_positions():
    _, skills = load_skill_templates()
    for skill in skills.values():
        enum_constraints = skill.get("enum_constraints") or {}
        for slot in ("source_anchor", "destination_anchor"):
            if slot not in enum_constraints:
                continue
            values = enum_constraints[slot]
            assert "left_effector" in values
            assert "right_effector" in values


def test_return_to_initial_pose_skill_is_available():
    _, skills = load_skill_templates()
    skill = skills["return_to_initial_pose"]

    assert skill["display_name"] == "回到初始位姿/复位"
    assert skill["template"] == "[subject] return to initial pose"
    assert skill["ui_template"] == "[subject] 回到初始位姿"
    assert skill["required_slots"] == ["subject"]
    assert skill["enum_constraints"]["subject"] == [
        "effector",
        "left_effector",
        "right_effector",
        "both_effectors",
        "unknown",
    ]
    assert skill["allowed_phase_actions"] == ["retreat", "idle"]


def test_zip_and_unzip_skills_are_available_with_simple_slots():
    _, skills = load_skill_templates()
    expected_phase_actions = [
        "approach",
        "align",
        "grasp",
        "secure",
        "pull_motion",
        "position",
        "release",
        "retreat",
    ]

    zip_skill = skills["zip"]
    assert zip_skill["template"] == (
        "[subject] zip [interaction_target] from [source_anchor] to [destination_anchor]"
    )
    assert zip_skill["ui_template"] == (
        "[subject] 拉上/闭合 [interaction_target]，从 [source_anchor] 到 [destination_anchor]"
    )
    assert zip_skill["required_slots"] == [
        "subject",
        "interaction_target",
        "source_anchor",
        "destination_anchor",
    ]
    assert zip_skill["allowed_phase_actions"] == expected_phase_actions

    unzip_skill = skills["unzip"]
    assert unzip_skill["template"] == (
        "[subject] unzip [interaction_target] from [source_anchor] to [destination_anchor]"
    )
    assert unzip_skill["ui_template"] == (
        "[subject] 拉开/打开 [interaction_target]，从 [source_anchor] 到 [destination_anchor]"
    )
    assert unzip_skill["required_slots"] == zip_skill["required_slots"]
    assert unzip_skill["allowed_phase_actions"] == expected_phase_actions


def test_common_tool_and_state_skills_are_available_with_simple_slots():
    _, skills = load_skill_templates()
    expected = {
        "open": {
            "template": "[subject] open [interaction_target]",
            "ui_template": "[subject] 打开 [interaction_target]",
            "required_slots": ["subject", "interaction_target"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "grasp",
                "secure",
                "pull_motion",
                "push_motion",
                "rotate_motion",
                "retreat",
            ],
        },
        "close": {
            "template": "[subject] close [interaction_target]",
            "ui_template": "[subject] 关闭 [interaction_target]",
            "required_slots": ["subject", "interaction_target"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "push_motion",
                "pull_motion",
                "position",
                "release",
                "retreat",
            ],
        },
        "scoop": {
            "template": "[subject] scoop [substance] from [source_container] with [tool]",
            "ui_template": "[subject] 用 [tool] 从 [source_container] 舀取 [substance]",
            "required_slots": ["subject", "substance", "source_container", "tool"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "position",
                "lower",
                "carry",
                "retreat",
            ],
        },
        "cut": {
            "template": "[subject] cut [interaction_target] with [tool]",
            "ui_template": "[subject] 用 [tool] 切割 [interaction_target]",
            "required_slots": ["subject", "interaction_target", "tool"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "press_motion",
                "slide_motion",
                "retreat",
            ],
        },
        "hold": {
            "template": "[subject] hold [interaction_target]",
            "ui_template": "[subject] 固定/保持 [interaction_target]",
            "required_slots": ["subject", "interaction_target"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "grasp",
                "secure",
                "idle",
                "release",
                "retreat",
            ],
        },
        "stir": {
            "template": "[subject] stir [substance] in [destination_container] with [tool]",
            "ui_template": "[subject] 用 [tool] 搅拌 [destination_container] 中的 [substance]",
            "required_slots": ["subject", "substance", "destination_container", "tool"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "position",
                "rotate_motion",
                "retreat",
            ],
        },
    }

    for skill_id, expected_skill in expected.items():
        skill = skills[skill_id]
        assert skill["template"] == expected_skill["template"]
        assert skill["ui_template"] == expected_skill["ui_template"]
        assert skill["required_slots"] == expected_skill["required_slots"]
        assert skill["allowed_phase_actions"] == expected_skill["allowed_phase_actions"]
