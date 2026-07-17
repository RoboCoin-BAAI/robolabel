from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QLabel

from lite_annotator.segment_editor import PhaseDialog, SegmentEditor

_APP = None


def app():
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def test_set_end_to_current_frame_uses_half_open_boundary():
    app()
    editor = SegmentEditor()
    editor.set_frame_count(406)
    editor.set_current_frame(405)

    editor.set_end_to_current_frame()

    assert editor.end_frame_input.value() == 406


def test_set_end_to_current_frame_clamps_to_frame_count_boundary():
    app()
    editor = SegmentEditor()
    editor.set_frame_count(406)
    editor.current_frame = 406

    editor.set_end_to_current_frame()

    assert editor.end_frame_input.value() == 406


def test_set_start_to_current_frame_reads_latest_bound_frame_source():
    app()
    editor = SegmentEditor()
    editor.set_frame_count(100)
    editor.set_current_frame(41)
    editor.bind_frame_source(lambda: 42)

    editor.set_start_to_current_frame()

    assert editor.start_frame_input.value() == 42


def test_phase_dialog_shows_subtask_start_frame_hint():
    app()

    dialog = PhaseDialog(
        frame_count=100,
        current_frame=42,
        subtask_start_frame=20,
        subtask_end_frame=60,
    )

    labels = [child.text() for child in dialog.findChildren(QLabel)]
    assert any("当前subtask范围: 20:60" in text for text in labels)
    assert any("起始帧: 20" in text for text in labels)
