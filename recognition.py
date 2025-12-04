import os
import time
import tempfile
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
from config import cfg
from camera import create_camera_capture
from hand import process_hands


def create_gesture_recognizer():
    if mp_tasks_python is None or mp_tasks_vision is None:
        print("No MediaPipe Tasks API (GestureRecognizer) available.")
        return None

    base_options = mp_tasks_python.BaseOptions(model_asset_path=cfg.MODEL_FILENAME)
    options = mp_tasks_vision.GestureRecognizerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=mp_tasks_vision.RunningMode.VIDEO,
    )
    return mp_tasks_vision.GestureRecognizer.create_from_options(options)



def to_mp_image(frame):
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    try:
        return mp.Image.create_from_array(image_rgb)
    except Exception:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            cv2.imwrite(tmp.name, frame)
            tmp_path = tmp.name
        try:
            return mp.Image.create_from_file(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def start_recognition():
    recognizer = create_gesture_recognizer()
    if recognizer is None:
        return

    cap = create_camera_capture()
    if cap is None:
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            mp_image = to_mp_image(frame)
            timestamp_ms = int(time.time() * 1000)
            recognition_result = recognizer.recognize_for_video(mp_image, timestamp_ms)
            frame = process_hands(frame, recognition_result)
            cv2.imshow("Gesture Recognizer - press q to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()