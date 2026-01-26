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
        self.window_size = 300 
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
                    output_category_mask=True
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
                    
                    # Extract mask
                    category_mask = result.category_mask.numpy_view()
                    
                    # Convert frame to RGBA
                    frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    
                    # Apply mask
                    # The user reported the previous logic inverted them (Person=Transparent, Bg=Solid).
                    # So we invert the condition.
                    # If category_mask contains 0 and 1, we want 255 (Visible) for the Person.
                    # We'll try explicitly selecting the index for "Person" which we assume is what was missing.
                    # If previous was (mask > 0.5) -> Person Transparent, then Person must be 0?
                    # Let's try inverting: 
                    is_person = category_mask > 0.5 
                    # If the user said they were transparent, then `is_person` calculated above was resulting in 0 for them.
                    # This means category_mask was <= 0.5 for them.
                    # So we'll invert the logic:
                    mask = (category_mask <= 0.5).astype(np.uint8) * 255
                    
                    # Alternatively, if we just want to flip whatever it was doing:
                    # mask = cv2.bitwise_not(mask) 
                    
                    # However, let's stick to the inverted comparison for clarity.
                    # Let's actually assume standard behavior: 0=Background, 1=Person.
                    # If that's true, (mask > 0.5) should have worked.
                    # Since it didn't, maybe 0=Person, 1=Background?
                    # So we use <= 0.5 to select Person (0).
                    
                    mask = (category_mask <= 0.5).astype(np.uint8) * 255
                    
                    # Smoothing the mask slightly
                    mask = cv2.GaussianBlur(mask, (5, 5), 0)
                    
                    frame_rgba[:, :, 3] = mask
                    
                    h, w, ch = frame_rgba.shape
                    bytes_per_line = ch * w
                    image = QImage(frame_rgba.data, w, h, bytes_per_line, QImage.Format_RGBA8888).copy()
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
