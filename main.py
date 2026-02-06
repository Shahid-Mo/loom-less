import sys
import cv2
import numpy as np
import time
import os

# Modern MediaPipe Tasks API
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    print("Warning: MediaPipe not found. Background removal disabled.")

from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget

class CircularCamera(QWidget):
    def __init__(self):
        super().__init__()

        # --- CONFIGURATION ---
        self.window_size = 250 
        self.fps = 60
        self.model_path = 'selfie_segmenter.task'
        self.use_mediapipe = False
        
        # --- BACKGROUND REMOVAL SETUP (NEW TASKS API) ---
        if HAS_MEDIAPIPE and os.path.exists(self.model_path):
            try:
                base_options = python.BaseOptions(model_asset_path=self.model_path)
                options = vision.ImageSegmenterOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.VIDEO,
                    output_category_mask=False,
                    output_confidence_masks=True
                )
                self.segmenter = vision.ImageSegmenter.create_from_options(options)
                self.use_mediapipe = True
                print("MediaPipe Tasks API: Active")
            except Exception as e:
                print(f"Warning: MediaPipe init failed ({e}). Running in normal mode.")
                self.use_mediapipe = False
        else:
            if not os.path.exists(self.model_path):
                print(f"Warning: Model file {self.model_path} not found.")

        # --- WINDOW SETUP ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(50, 50, self.window_size, self.window_size)

        # --- OPENCV SETUP (Auto-Detect) ---
        self.cap = None
        for idx in [0, 1, 2]:
            temp_cap = cv2.VideoCapture(idx)
            if temp_cap.isOpened():
                ret, _ = temp_cap.read()
                if ret:
                    print(f"Success: Camera found at index {idx}")
                    self.cap = temp_cap
                    break
                else:
                    temp_cap.release()
            
        if self.cap is None:
            print("\nError: No working camera found.")
            sys.exit(1)
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / self.fps))

        self.old_pos = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # 1. Flip horizontally (Mirror effect)
            frame = cv2.flip(frame, 1)

            # 2. Crop to square (Center Crop)
            h, w, _ = frame.shape
            min_dim = min(h, w)
            start_x = (w - min_dim) // 2
            start_y = (h - min_dim) // 2
            frame = frame[start_y:start_y+min_dim, start_x:start_x+min_dim]

            # 3. Resize to window size
            frame = cv2.resize(frame, (self.window_size, self.window_size))
            
            # 4. Background Removal
            if self.use_mediapipe:
                try:
                    # Convert to RGB for MediaPipe
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                    
                    # Run segmentation
                    timestamp_ms = int(time.time() * 1000)
                    result = self.segmenter.segment_for_video(mp_image, timestamp_ms)
                    
                    # Extract confidence mask (soft probabilities 0.0-1.0)
                    # Index 0 = background, index 1 = person (if available)
                    confidence_masks = result.confidence_masks
                    if len(confidence_masks) > 1:
                        person_mask = confidence_masks[1].numpy_view()
                    else:
                        person_mask = confidence_masks[0].numpy_view()

                    # Convert frame to RGBA
                    frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

                    # Smooth the soft mask for clean edges
                    mask_u8 = (person_mask * 255).astype(np.uint8)

                    # 1. Threshold to get a solid core mask
                    _, solid = cv2.threshold(mask_u8, 128, 255, cv2.THRESH_BINARY)

                    # 2. Light erode to trim outermost fringe
                    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    solid = cv2.erode(solid, erode_kernel, iterations=1)

                    # 3. Close small holes (hair strands)
                    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, close_kernel)

                    # 4. Blur for feathered edges
                    mask = cv2.GaussianBlur(solid, (11, 11), 3)

                    # 5. Premultiply RGB by alpha to avoid bg-color halo
                    alpha_f = mask.astype(np.float32) / 255.0
                    for c in range(3):
                        frame_rgba[:, :, c] = (frame_rgba[:, :, c].astype(np.float32) * alpha_f).astype(np.uint8)
                    frame_rgba[:, :, 3] = mask
                    
                    h, w, ch = frame_rgba.shape
                    bytes_per_line = ch * w
                    image = QImage(frame_rgba.data, w, h, bytes_per_line, QImage.Format_RGBA8888_Premultiplied).copy()
                    self.current_frame = image
                except Exception as e:
                    print(f"MediaPipe Runtime Error: {e}")
                    self.use_mediapipe = False 
            
            if not self.use_mediapipe:
                # Normal Mode (No Background Removal)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.current_frame = image
            
            self.update()

    def paintEvent(self, event):
        if hasattr(self, 'current_frame'):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, self.window_size, self.window_size)
            painter.setClipPath(path)
            painter.drawImage(0, 0, self.current_frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            self.close()

    def closeEvent(self, event):
        if hasattr(self, 'segmenter'):
            self.segmenter.close()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CircularCamera()
    window.show()
    sys.exit(app.exec_())
