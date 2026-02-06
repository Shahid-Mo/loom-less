# Circular Cam

A lightweight, high-performance circular camera overlay for macOS. Perfect for tutorials, screen recordings, and presentations.

## Features
- **Circular Mask**: No black corners, perfect circle.
- **Background Removal**: Automatically removes your background using AI (MediaPipe) with smooth, feathered edges via confidence masks and premultiplied alpha.
- **Mirrored View**: Acts like a natural mirror.
- **Always on Top**: Floats above all windows (VS Code, browser, etc.).
- **Draggable**: Click and drag anywhere on the camera feed to move it.
- **High FPS**: smooth 60fps rendering.

## Prerequisites
- macOS (M1/M2/M3 or Intel)
- Python 3.12+
- Camera permissions for your terminal/IDE.

## Setup & Run

We use `uv` for fast package management.

```bash
# Clone the repo (if applicable)
# git clone ...
# cd circular_cam

# Run the app
uv run main.py
```

## Controls
- **Move**: Click and drag.
- **Close**: Press `ESC` or `Q`.

## Troubleshooting (macOS)
If the window is black, macOS might be blocking camera access.
1. Go to **System Settings > Privacy & Security > Camera**.
2. Ensure your Terminal or IDE (e.g., VS Code) is toggled **ON**.