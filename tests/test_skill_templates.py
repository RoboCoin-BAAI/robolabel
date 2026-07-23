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
    assert skill["allowed_phase_actions"] == ["retreat"]


def test_zip_and_unzip_skills_are_available_with_simple_slots():
    _, skills = load_skill_templates()
    expected_phase_actions = [
        "pull_motion",
        "release",
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
            "template": "[subject] open [interaction_target] with [physical_motion]",
            "ui_template": "[subject] 用 [physical_motion] 打开 [interaction_target]",
            "required_slots": ["subject", "interaction_target", "physical_motion"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "grasp",
                "pull_motion",
                "push_motion",
                "press_motion",
                "release",
            ],
        },
        "close": {
            "template": "[subject] close [interaction_target] with [physical_motion]",
            "ui_template": "[subject] 用 [physical_motion] 关闭 [interaction_target]",
            "required_slots": ["subject", "interaction_target", "physical_motion"],
            "allowed_phase_actions": [
                "approach",
                "align",
                "grasp",
                "pull_motion",
                "push_motion",
                "press_motion",
                "release",
            ],
        },
        "scoop": {
            "template": "[subject] scoop [substance] from [source_container] with [tool]",
            "ui_template": "[subject] 用 [tool] 从 [source_container] 舀取 [substance]",
            "required_slots": ["subject", "substance", "source_container", "tool"],
            "allowed_phase_actions": [
                "carry",
                "align",
                "rotate_motion",
                "slide_motion",
                "lift",
            ],
        },
        "cut": {
            "template": "[subject] cut [interaction_target] with [tool]",
            "ui_template": "[subject] 用 [tool] 切割 [interaction_target]",
            "required_slots": ["subject", "interaction_target", "tool"],
            "allowed_phase_actions": [
                "carry",
                "align",
                "press_motion",
                "slide_motion",
                "lift",
            ],
        },
        "hold": {
            "template": "[subject] hold [interaction_target]",
            "ui_template": "[subject] 固定/保持 [interaction_target]",
            "required_slots": ["subject", "interaction_target"],
            "allowed_phase_actions": [
                "secure",
            ],
        },
        "stir": {
            "template": "[subject] stir [substance] in [destination_container] with [tool]",
            "ui_template": "[subject] 用 [tool] 搅拌 [destination_container] 中的 [substance]",
            "required_slots": ["subject", "substance", "destination_container", "tool"],
            "allowed_phase_actions": [
                "carry",
                "align",
                "insert_motion",
                "rotate_motion",
            ],
        },
    }

    for skill_id, expected_skill in expected.items():
        skill = skills[skill_id]
        assert skill["template"] == expected_skill["template"]
        assert skill["ui_template"] == expected_skill["ui_template"]
        assert skill["required_slots"] == expected_skill["required_slots"]
        assert skill["allowed_phase_actions"] == expected_skill["allowed_phase_actions"]

    for skill_id in ("open", "close"):
        skill = skills[skill_id]
        assert skill["slot_display_names"]["physical_motion"] == "物理动作方式"
        assert skill["enum_constraints"]["physical_motion"] == [
            "pull_motion",
            "push_motion",
            "press_motion",
        ]
        assert skill["enum_display_names"]["physical_motion"] == {
            "pull_motion": "拉动",
            "push_motion": "推动",
            "press_motion": "按压",
        }

def test_hand_over_skill_is_available_with_receiver_slot():
    _, skills = load_skill_templates()
    skill = skills["hand_over"]

    assert skill["display_name"] == "递交/交接"
    assert skill["template"] == "[subject] hand over [manipulated_object] to [destination_anchor]"
    assert skill["ui_template"] == "[subject] 将 [manipulated_object] 递交给 [destination_anchor]"
    assert skill["required_slots"] == [
        "subject",
        "manipulated_object",
        "destination_anchor",
    ]
    assert skill["slot_display_names"]["destination_anchor"] == "接收方/目标位置"
    assert "left_effector" in skill["enum_constraints"]["destination_anchor"]
    assert "right_effector" in skill["enum_constraints"]["destination_anchor"]
    assert skill["allowed_phase_actions"] == [
        "align",
        "grasp",
        "release",
    ]


def test_skill_phase_actions_follow_carry_when_holding_object_or_tool_rule():
    _, skills = load_skill_templates()

    assert skills["hold"]["allowed_phase_actions"] == ["secure"]
    assert skills["transfer"]["allowed_phase_actions"] == ["carry"]
    assert skills["twist"]["allowed_phase_actions"] == ["rotate_motion"]
    assert skills["pick"]["allowed_phase_actions"] == ["approach", "align", "grasp"]
    assert skills["place"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "release",
    ]
    assert skills["press"]["allowed_phase_actions"] == ["approach", "align", "press_motion"]
    assert skills["push"]["allowed_phase_actions"] == ["approach", "align", "push_motion"]
    assert skills["pull"]["allowed_phase_actions"] == [
        "approach",
        "align",
        "pull_motion",
    ]
    assert skills["pour"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "tilt_motion",
        "pour_motion",
    ]
    assert skills["fold"]["allowed_phase_actions"] == [
        "approach",
        "align",
        "grasp",
        "fold_motion",
        "release",
    ]
    assert skills["slide"]["allowed_phase_actions"] == [
        "approach",
        "align",
        "grasp",
        "slide_motion",
        "release",
    ]
    assert skills["insert"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "insert_motion",
        "release",
    ]
    assert skills["shake"]["allowed_phase_actions"] == [
        "secure",
        "shake_motion",
        "release",
    ]
    assert skills["strike"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "strike_motion",
    ]
    assert skills["throw"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "release",
    ]
    assert skills["wipe_scrub"]["allowed_phase_actions"] == [
        "carry",
        "align",
        "scrub_motion",
        "release",
    ]


def test_optional_phase_actions_are_marked_in_skill_templates():
    _, skills = load_skill_templates()

    expected_optional = {
        "pick": ["align"],
        "place": ["align"],
        "press": ["align"],
        "push": ["align"],
        "pull": ["align"],
        "open": ["align", "release"],
        "close": ["align", "release"],
        "scoop": ["align"],
        "cut": ["align", "slide_motion"],
        "stir": ["align", "insert_motion"],
        "pour": ["align"],
        "fold": ["align", "release"],
        "slide": ["align", "release"],
        "insert": ["align", "release"],
        "shake": ["release"],
        "strike": ["align"],
        "throw": ["align"],
        "hand_over": ["align"],
        "wipe_scrub": ["align", "release"],
    }

    for skill_id, optional_actions in expected_optional.items():
        skill = skills[skill_id]
        assert skill.get("optional_phase_actions") == optional_actions
        for phase_action in optional_actions:
            assert phase_action in skill["allowed_phase_actions"]
