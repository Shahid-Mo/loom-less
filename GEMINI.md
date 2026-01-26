# Circular Cam

A lightweight, circular camera overlay for macOS built with Python, PyQt5, and OpenCV.

## Project Goal
Create a borderless, draggable, circular camera window that stays on top of other applications, providing a clean "talking head" overlay for screen recordings or presentations.

## Tech Stack
- **Python**: Core language.
- **PyQt5**: For the GUI, handling transparency, and "always on top" window behavior.
- **OpenCV (cv2)**: For capturing and processing camera frames.
- **uv**: Package management.

## Current Progress
- Project initialized.
- Dependencies (`opencv-python`, `PyQt5`) installed via `uv`.
- Implementation complete in `main.py`.

## Planned Features
- [x] Implement circular camera window.
- [x] Support for window dragging.
- [x] Hardware acceleration and high FPS (60fps target).
- [x] Camera selection logic.
- [x] Exit via 'ESC' or 'Q'.
- [x] Fix inverted camera (mirror mode).
- [x] Improved "Always on Top" (removed Qt.Tool).
- [x] Background Removal (MediaPipe).

## How to Run
```bash
uv run main.py
```
