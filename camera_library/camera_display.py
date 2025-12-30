import cv2
from configuration.configuration import cfg
from mediapipe.framework.formats import landmark_pb2


def convert_hand_landmarks_proto_to_drawable(hand_landmarks_proto):
    return hand_landmarks_proto

def create_camera_capture():
    cap = cv2.VideoCapture(cfg.camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Unable to open camera.")
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.camera_width_default)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.camera_height_default)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera {cfg.camera_index}: {actual_w}x{actual_h}")
    cv2.setUseOptimized(True)
    return cap

def to_landmark_proto(hand_lms):
    if isinstance(hand_lms, landmark_pb2.NormalizedLandmarkList):
        return hand_lms
    proto = landmark_pb2.NormalizedLandmarkList()
    for lm in hand_lms:
        proto.landmark.add(x=lm.x, y=lm.y, z=getattr(lm, "z", 0.0))
    return proto

def draw_corner_labels(frame, w, left_corner_text, right_corner_text):
    frame = cv2.flip(frame, 1)
    if left_corner_text:
        cv2.putText(frame, left_corner_text, (10, 30), cfg.font, cfg.font_scale, (255, 0, 0), cfg.thickness, cv2.LINE_AA)

    if right_corner_text:
        (tw, _), _ = cv2.getTextSize(right_corner_text, cfg.font, cfg.font_scale, cfg.thickness)
        cv2.putText(frame, right_corner_text, (w - tw - 10, 30), cfg.font, cfg.font_scale, (0, 0, 255), cfg.thickness, cv2.LINE_AA)

    return frame

def extract_lists(recognition_result):
    gestures_list = recognition_result.gestures or []
    handedness_list = recognition_result.handedness or []
    landmarks_list = recognition_result.hand_landmarks or []
    return gestures_list, handedness_list, landmarks_list

def get_labels(top_gesture_text, hand_label, finger_gesture_text, left_corner_text=None, right_corner_text=None):
    label = f"{hand_label}: {top_gesture_text}" if top_gesture_text else f"{hand_label}: -"
    if finger_gesture_text:
        label = f"{label} | {finger_gesture_text}"
    if hand_label == "Left":
        left_corner_text = label
    elif hand_label == "Right":
        right_corner_text = label
    return left_corner_text, right_corner_text

