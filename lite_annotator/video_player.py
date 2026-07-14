from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class VideoPlayer(QWidget):
    frame_changed = pyqtSignal(int)
    video_loaded = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

        self.image_label = QLabel("No video loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 360)

        self.frame_label = QLabel("Frame: -/-")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.seek)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)
        self.prev_button = QPushButton("Prev")
        self.prev_button.clicked.connect(self.previous_frame)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_frame)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.frame_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        layout.addWidget(self.slider)
        layout.addLayout(controls)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def load_video(self, path: str | Path) -> None:
        import cv2

        capture = cv2.VideoCapture(str(path))
        frames = []
        success, frame = capture.read()
        while success:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            success, frame = capture.read()
        capture.release()
        if not frames:
            raise RuntimeError(f"Could not decode video: {path}")

        self.timer.stop()
        self.play_button.setText("Play")
        self.frames = frames
        self.current_frame = 0
        self.slider.blockSignals(True)
        self.slider.setRange(0, len(frames) - 1)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.show_frame(0)
        self.video_loaded.emit(len(frames))

    def show_frame(self, index: int) -> None:
        if not self.frames:
            return
        index = max(0, min(index, len(self.frames) - 1))
        self.current_frame = index
        frame = self.frames[index]
        height, width, channels = frame.shape
        image = QImage(frame.data, width, height, channels * width, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)
        self.frame_label.setText(f"Frame: {index + 1}/{len(self.frames)}")
        self.slider.blockSignals(True)
        self.slider.setValue(index)
        self.slider.blockSignals(False)
        self.frame_changed.emit(index)

    def seek(self, index: int) -> None:
        self.show_frame(index)

    def next_frame(self) -> None:
        if not self.frames:
            return
        if self.current_frame >= len(self.frames) - 1:
            self.timer.stop()
            self.play_button.setText("Play")
            return
        self.show_frame(self.current_frame + 1)

    def previous_frame(self) -> None:
        self.show_frame(self.current_frame - 1)

    def toggle_playback(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText("Play")
        else:
            self.timer.start(50)
            self.play_button.setText("Pause")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_frame(self.current_frame)
