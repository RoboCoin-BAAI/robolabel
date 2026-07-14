from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QCompleter,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from common.skill_schema import (
    build_action_from_slot_values,
    load_skill_templates,
    render_subtask_text,
)
from lite_annotator.ui_text import bilingual_label

TEMPLATE_SET_VERSION, SKILL_TEMPLATES = load_skill_templates()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OBJECT_SLOT_PATH = PROJECT_ROOT / "config" / "skill_object_slots.json"


def load_object_slot_keys(path=DEFAULT_OBJECT_SLOT_PATH):
    path = Path(path)
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(item) for item in data.get("object_slots", [])}


OBJECT_SLOT_KEYS = load_object_slot_keys()


class SkillForm(QWidget):
    def __init__(self, parent=None, scene_object_options=None):
        super().__init__(parent)
        self.slot_widgets = {}
        self.scene_object_options = scene_object_options or {}
        self.skill_select = QComboBox()
        for skill_id, skill in SKILL_TEMPLATES.items():
            if skill_id == "custom":
                continue
            self.skill_select.addItem(
                f"{skill.get('display_name', skill_id)} ({skill_id})",
                skill_id,
            )
        self.skill_select.currentIndexChanged.connect(self.render_slots)

        self.form_layout = QFormLayout()
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(90)

        layout = QVBoxLayout(self)
        layout.addWidget(self.skill_select)
        layout.addLayout(self.form_layout)
        layout.addWidget(self.preview)
        self.render_slots()

    def current_skill_id(self):
        return self.skill_select.currentData()

    def render_slots(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.slot_widgets = {}
        skill = SKILL_TEMPLATES[self.current_skill_id()]
        for slot in skill["required_slots"]:
            editor = self.create_slot_editor(skill, slot)
            self.slot_widgets[slot] = editor
            label = bilingual_label(skill.get("slot_display_names", {}).get(slot, slot), slot)
            self.form_layout.addRow(label, editor)
        self.update_preview()

    def create_slot_editor(self, skill, slot):
        if slot in OBJECT_SLOT_KEYS and self.scene_object_options:
            editor = QComboBox()
            editor.setEditable(True)
            editor.setInsertPolicy(QComboBox.NoInsert)
            for value, label in self.scene_object_options.items():
                editor.addItem(bilingual_label(label, value), value)
            self.attach_combo_completer(editor)
            editor.currentIndexChanged.connect(self.update_preview)
            editor.editTextChanged.connect(self.update_preview)
            return editor

        allowed_values = skill.get("enum_constraints", {}).get(slot)
        if allowed_values:
            editor = QComboBox()
            editor.setEditable(True)
            editor.setInsertPolicy(QComboBox.NoInsert)
            display_names = skill.get("enum_display_names", {}).get(slot, {})
            for value in allowed_values:
                editor.addItem(
                    bilingual_label(display_names.get(value, value), value),
                    value,
                )
            if slot == "destination_anchor" and self.scene_object_options:
                for value, label in self.scene_object_options.items():
                    if editor.findData(value) < 0:
                        editor.addItem(bilingual_label(label, value), value)
            self.attach_combo_completer(editor)
            editor.currentIndexChanged.connect(self.update_preview)
            editor.editTextChanged.connect(self.update_preview)
            return editor

        editor = QLineEdit()
        editor.textChanged.connect(self.update_preview)
        return editor

    def attach_combo_completer(self, combo):
        completer = QCompleter([combo.itemText(index) for index in range(combo.count())], combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)

    def widget_value(self, widget):
        if isinstance(widget, QComboBox):
            text = widget.currentText().strip()
            for index in range(widget.count()):
                if text in (widget.itemText(index), str(widget.itemData(index))):
                    return str(widget.itemData(index) or "").strip()
            return text
        return widget.text().strip()

    def set_widget_value(self, widget, value):
        value = str(value)
        if isinstance(widget, QComboBox):
            for index in range(widget.count()):
                if str(widget.itemData(index)) == value:
                    widget.setCurrentIndex(index)
                    return
            widget.setEditText(value)
            return
        widget.setText(value)

    def clear_values(self):
        for widget in self.slot_widgets.values():
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.clear()
        self.update_preview()

    def load_subtask(self, subtask):
        self.clear_values()
        actions = (subtask or {}).get("actions") or []
        if not actions:
            return

        action = actions[0]
        skill_id = action.get("skill")
        for index in range(self.skill_select.count()):
            if self.skill_select.itemData(index) == skill_id:
                self.skill_select.setCurrentIndex(index)
                break

        slots = action.get("slots") or {}
        subject = action.get("subject", "")
        if "subject" in self.slot_widgets:
            self.set_widget_value(self.slot_widgets["subject"], subject)
        for key, value in slots.items():
            if key in self.slot_widgets:
                self.set_widget_value(self.slot_widgets[key], value)
        self.update_preview()

    def build_subtask(self, start_frame, end_frame):
        values = {
            key: self.widget_value(widget)
            for key, widget in self.slot_widgets.items()
        }
        action = build_action_from_slot_values(
            self.current_skill_id(),
            values,
            SKILL_TEMPLATES,
        )
        actions = [action]
        return {
            "start_frame": int(start_frame),
            "end_frame": int(end_frame),
            "coordination_mode": "single_hand",
            "actions": actions,
            "text": render_subtask_text(actions),
        }

    def update_preview(self):
        try:
            subtask = self.build_subtask(0, 0)
            self.preview.setText(subtask["text"])
        except Exception as exc:
            self.preview.setText(str(exc))
