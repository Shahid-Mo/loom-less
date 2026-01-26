import mediapipe as mp
print(dir(mp))
try:
    import mediapipe.python.solutions.selfie_segmentation
    print("Direct import: OK")
except ImportError as e:
    print(f"Direct import failed: {e}")
