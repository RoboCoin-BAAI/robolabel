from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import cv2
import numpy as np


def read_video_rgb_frames(path: str | Path) -> list[np.ndarray]:
    video_path = Path(path)
    frames = read_video_with_opencv(video_path)
    if frames:
        return frames
    return read_video_with_ffmpeg(video_path)


def decode_video_frames(path: str | Path) -> list[np.ndarray]:
    return read_video_rgb_frames(path)


def read_video_with_opencv(path: Path) -> list[np.ndarray]:
    with muted_stderr():
        capture = cv2.VideoCapture(str(path))
        frames = []
        success, frame = capture.read()
        while success:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            success, frame = capture.read()
        capture.release()
        return frames


def read_video_with_ffmpeg(path: Path) -> list[np.ndarray]:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError(
            f"Could not decode video: {path}. OpenCV could not read this codec, "
            "and ffmpeg/ffprobe is not available."
        )

    width, height = probe_video_size(path)
    frame_size = width * height * 3
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-vsync",
        "0",
        "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None

    frames = []
    while True:
        chunk = process.stdout.read(frame_size)
        if not chunk:
            break
        if len(chunk) != frame_size:
            process.kill()
            raise RuntimeError(f"Could not decode complete frame from video: {path}")
        frame = np.frombuffer(chunk, dtype=np.uint8).reshape((height, width, 3)).copy()
        frames.append(frame)

    _, stderr = process.communicate()
    if process.returncode != 0 or not frames:
        message = stderr.decode("utf-8", errors="replace").strip()
        detail = f" ffmpeg: {message}" if message else ""
        raise RuntimeError(f"Could not decode video: {path}.{detail}")
    return frames


def probe_video_size(path: Path) -> tuple[int, int]:
    command = [
        "ffprobe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    info = json.loads(result.stdout)
    stream = (info.get("streams") or [{}])[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Could not probe video size: {path}")
    return width, height


@contextmanager
def muted_stderr():
    saved_stderr = os.dup(2)
    try:
        with open(os.devnull, "w") as devnull:
            os.dup2(devnull.fileno(), 2)
            yield
    finally:
        os.dup2(saved_stderr, 2)
        os.close(saved_stderr)
