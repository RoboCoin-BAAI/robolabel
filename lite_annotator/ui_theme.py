from __future__ import annotations

APP_NAME = "robolabletools"


APP_STYLESHEET = """
QWidget {
    background: #f4f6f7;
    color: #1f2933;
    font-size: 13px;
}

QMainWindow {
    background: #eef2f3;
}

QLabel {
    color: #26323a;
}

QPushButton {
    background: #256f6f;
    color: #ffffff;
    border: 1px solid #1c5c5c;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
}

QPushButton:hover {
    background: #2d8181;
}

QPushButton:pressed {
    background: #1c5c5c;
}

QPushButton:disabled {
    background: #cbd5da;
    color: #6b7780;
    border-color: #b8c4ca;
}

QLineEdit,
QTextEdit,
QComboBox,
QSpinBox,
QListWidget,
QTableWidget {
    background: #ffffff;
    color: #1f2933;
    border: 1px solid #c6d0d5;
    border-radius: 5px;
    selection-background-color: #d7ece9;
    selection-color: #102a2a;
}

QLineEdit,
QComboBox,
QSpinBox {
    min-height: 26px;
    padding: 2px 6px;
}

QSpinBox {
    padding-right: 24px;
}

QSpinBox::up-button,
QSpinBox::down-button {
    subcontrol-origin: border;
    width: 22px;
    background: #e1ecec;
    border-left: 1px solid #9bb0b8;
}

QSpinBox::up-button {
    subcontrol-position: top right;
    border-top-right-radius: 5px;
    border-bottom: 1px solid #9bb0b8;
}

QSpinBox::down-button {
    subcontrol-position: bottom right;
    border-bottom-right-radius: 5px;
}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover {
    background: #cde4e1;
}

QSpinBox::up-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid #1c5c5c;
}

QSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #1c5c5c;
}

QTextEdit,
QListWidget,
QTableWidget {
    padding: 4px;
}

QHeaderView::section {
    background: #dfe7ea;
    color: #22313a;
    border: 0;
    border-right: 1px solid #c6d0d5;
    border-bottom: 1px solid #c6d0d5;
    padding: 6px;
}

QGroupBox {
    border: 1px solid #c6d0d5;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 10px;
    background: #f9fbfb;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #1c5c5c;
}

QSlider::groove:horizontal {
    background: #c6d0d5;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #256f6f;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QScrollBar:vertical,
QScrollBar:horizontal {
    background: #edf1f2;
    border: 0;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background: #aebdc4;
    border-radius: 4px;
}
"""


def apply_app_theme(app) -> None:
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(APP_STYLESHEET)
