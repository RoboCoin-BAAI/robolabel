from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lite_annotator.ui_text import bilingual_label
from lite_annotator.vocabulary import option_label


class MultiCameraVideoPlayer(QWidget):
    frame_changed = pyqtSignal(int)
    episode_loaded = pyqtSignal(int)
    MAIN_FRAME_SIZE = (640, 360)
    AUX_FRAME_SIZE = (320, 180)
    TITLE_HEIGHT = 22

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames_by_camera: dict[str, list] = {}
        self.main_camera: str | None = None
        self.current_subtask: dict | None = None
        self.object_display_labels: dict[str, str] = {}
        self.action_display_labels: dict[str, str] = {}
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

        self.video_grid = QGridLayout()
        self.camera_labels: dict[str, QLabel] = {}
        self.camera_containers: dict[str, QWidget] = {}
        self.frame_label = QLabel(f"{bilingual_label('帧', 'frame')}: -/-")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.seek)

        self.play_button = QPushButton(bilingual_label("播放", "play"))
        self.play_button.clicked.connect(self.toggle_playback)
        self.prev_button = QPushButton(bilingual_label("上一帧", "prev"))
        self.prev_button.clicked.connect(self.previous_frame)
        self.next_button = QPushButton(bilingual_label("下一帧", "next"))
        self.next_button.clicked.connect(self.next_frame)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.frame_label)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_panel = QWidget()
        self.info_panel.setFixedWidth(self.MAIN_FRAME_SIZE[0])
        self.info_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.info_panel.setStyleSheet(
            "background-color: #f9fbfb; border: 1px solid #c6d0d5; border-radius: 6px;"
        )
        info_layout = QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(8, 6, 8, 6)
        info_layout.addWidget(self.info_label)

        self.video_column = QWidget()
        self.video_column.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        video_column_layout = QVBoxLayout(self.video_column)
        video_column_layout.setContentsMargins(0, 0, 0, 0)
        video_column_layout.addLayout(self.video_grid)
        video_column_layout.addWidget(self.slider)
        video_column_layout.addLayout(controls)
        video_column_layout.addWidget(self.info_panel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_column, 0, Qt.AlignTop | Qt.AlignHCenter)
        self.set_placeholder()

    @property
    def frame_count(self) -> int:
        if not self.frames_by_camera:
            return 0
        return min(len(frames) for frames in self.frames_by_camera.values())

    def set_placeholder(self):
        self.clear_grid()
        label = QLabel(bilingual_label("未加载数据条目", "no episode loaded"))
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumSize(640, 360)
        self.video_grid.addWidget(label, 0, 0)
        self.camera_labels = {"__placeholder__": label}
        self.set_current_subtask(None)

    def clear_grid(self):
        while self.video_grid.count():
            item = self.video_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_episode(self, camera_videos: dict[str, Path], main_camera: str | None = None) -> None:
        if not camera_videos:
            raise RuntimeError("No camera videos selected")
        if len(camera_videos) > 3:
            raise RuntimeError("最多选择 3 个相机")

        import cv2

        loaded: dict[str, list] = {}
        for camera, video_path in camera_videos.items():
            capture = cv2.VideoCapture(str(video_path))
            frames = []
            success, frame = capture.read()
            while success:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                success, frame = capture.read()
            capture.release()
            if not frames:
                raise RuntimeError(f"Could not decode video: {video_path}")
            loaded[camera] = frames

        self.timer.stop()
        self.play_button.setText(bilingual_label("播放", "play"))
        self.frames_by_camera = loaded
        self.main_camera = main_camera if main_camera in loaded else next(iter(loaded))
        self.current_frame = 0
        self.rebuild_camera_grid()
        self.slider.blockSignals(True)
        self.slider.setRange(0, self.frame_count - 1)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.show_frame_after_layout()
        self.set_current_subtask(None)
        self.episode_loaded.emit(self.frame_count)

    def rebuild_camera_grid(self):
        self.clear_grid()
        self.camera_labels = {}
        self.camera_containers = {}
        for column in range(2):
            self.video_grid.setColumnStretch(column, 0)
        for row in range(2):
            self.video_grid.setRowStretch(row, 0)
        for index, camera in enumerate(self.ordered_cameras()):
            is_main = index == 0
            frame_size = self.MAIN_FRAME_SIZE if is_main else self.AUX_FRAME_SIZE
            container = QWidget()
            container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            title = QLabel(camera)
            title.setAlignment(Qt.AlignCenter)
            title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            title.setFixedHeight(self.TITLE_HEIGHT)
            image = QLabel()
            image.setAlignment(Qt.AlignCenter)
            image.setFixedSize(*frame_size)
            image.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            image.setStyleSheet("background-color: #111;")
            layout.addWidget(title, 0)
            layout.addWidget(image, 0)
            if is_main:
                self.video_grid.addWidget(container, 0, 0, 1, 2, Qt.AlignHCenter | Qt.AlignTop)
            else:
                self.video_grid.addWidget(container, 1, index - 1, Qt.AlignHCenter | Qt.AlignTop)
            self.camera_labels[camera] = image
            self.camera_containers[camera] = container

    def ordered_cameras(self) -> list[str]:
        cameras = list(self.frames_by_camera)
        if not cameras:
            return []
        main_camera = self.main_camera if self.main_camera in self.frames_by_camera else cameras[0]
        return [main_camera] + [camera for camera in cameras if camera != main_camera]

    def show_frame_after_layout(self) -> None:
        QTimer.singleShot(0, lambda: self.show_frame(self.current_frame))

    def set_current_subtask(self, subtask: dict | None) -> None:
        self.current_subtask = subtask
        self.refresh_current_subtask_label()

    def set_display_label_maps(self, object_options=None, action_options=None) -> None:
        self.object_display_labels = dict(object_options or {})
        self.action_display_labels = dict(action_options or {})
        self.refresh_current_subtask_label()

    def display_value(self, value, labels):
        value = str(value or "")
        return option_label(value, labels.get(value, value)) if value else ""

    def refresh_current_subtask_label(self) -> None:
        subtask = self.current_subtask
        if not subtask:
            self.info_label.setText(bilingual_label("未选择subtask", "no subtask selected"))
            return
        start = int(subtask.get("start_frame", 0))
        end = int(subtask.get("end_frame", 0))
        text = subtask.get("text", "")
        lines = [
            "  |  ".join([
                bilingual_label("当前subtask", "current subtask"),
                f"{start}-{end}",
                text,
            ])
        ]
        phases = subtask.get("phases") or []
        if phases:
            lines.append("phase:")
            for index, phase in enumerate(phases, start=1):
                phase_start = int(phase.get("start_frame", 0))
                phase_end = int(phase.get("end_frame", 0))
                lines.append(
                    f"{index}. {phase_start}-{phase_end}  "
                    f"{self.display_value(phase.get('action', ''), self.action_display_labels)}  "
                    f"{self.display_value(phase.get('object', ''), self.object_display_labels)}"
                )
        self.info_label.setText("\n".join(lines))

    def show_frame(self, index: int) -> None:
        if not self.frames_by_camera:
            return
        index = max(0, min(index, self.frame_count - 1))
        self.current_frame = index
        for camera, frames in self.frames_by_camera.items():
            frame = frames[index]
            height, width, channels = frame.shape
            image = QImage(frame.data, width, height, channels * width, QImage.Format_RGB888)
            label = self.camera_labels[camera]
            pixmap = QPixmap.fromImage(image).scaled(
                label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            label.setPixmap(pixmap)
        self.frame_label.setText(f"{bilingual_label('帧', 'frame')}: {index}/{self.frame_count - 1}")
        self.slider.blockSignals(True)
        self.slider.setValue(index)
        self.slider.blockSignals(False)
        self.frame_changed.emit(index)

    def seek(self, index: int) -> None:
        self.show_frame(index)

    def next_frame(self) -> None:
        if not self.frames_by_camera:
            return
        if self.current_frame >= self.frame_count - 1:
            self.timer.stop()
            self.play_button.setText(bilingual_label("播放", "play"))
            return
        self.show_frame(self.current_frame + 1)

    def previous_frame(self) -> None:
        self.show_frame(self.current_frame - 1)

    def toggle_playback(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText(bilingual_label("播放", "play"))
        else:
            self.timer.start(50)
            self.play_button.setText(bilingual_label("暂停", "pause"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_frame(self.current_frame)
