import cv2
import mediapipe as mp

print(f"OpenCV Version: {cv2.__version__}")
if hasattr(cv2, 'VideoCapture'):
    print("VideoCapture: OK")
else:
    print("VideoCapture: MISSING")

if hasattr(mp, 'solutions'):
    print("MediaPipe Solutions: OK")
else:
    print("MediaPipe Solutions: MISSING")
