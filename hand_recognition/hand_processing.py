from configuration.configuration import cfg
from configuration.function_assigne.function_configuration import select_and_call_func
from function_library.math_functions import should_calculate_angle, calculate_pointer_angle
from camera_library.camera_display import draw_corner_labels, get_labels, to_landmark_proto, extract_lists
from function_library.trigerable_functions import update_mouse_movement, is_applied_boost
from hand_recognition.manual_hand_recognition import detect_finger_gesture
import traceback
import os
import cv2
import time
import logging

# Setup logging
logging.basicConfig(
    filename='debug_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

_last_logged_gesture_by_hand = {}

def _log_gesture_change(hand_label: str, top_gesture, finger_gesture_text: str, frame=None):
    top_name = getattr(top_gesture, "category_name", "") if top_gesture else ""
    top_score = getattr(top_gesture, "score", None) if top_gesture else None

    parts = [hand_label or "Unknown"]
    if top_name:
        parts.append(f"mp:{top_name}" + (f"({top_score:.2f})" if isinstance(top_score, (int, float)) else ""))
    if finger_gesture_text:
        parts.append(f"manual:{finger_gesture_text}")

    msg = " | ".join(parts) if len(parts) > 1 else f"{hand_label or 'Unknown'} | -"

    prev = _last_logged_gesture_by_hand.get(hand_label)
    if prev != msg:
        _last_logged_gesture_by_hand[hand_label] = msg
        if cfg.debug_mode:
            print(f"[gesture] {msg}")
            logging.info(f"[gesture] {msg}")
            
            if frame is not None and (top_name or finger_gesture_text):
                try:
                    if not os.path.exists("debug_images"):
                        os.makedirs("debug_images")
                    timestamp = int(time.time() * 1000)
                    filename = f"debug_images/{timestamp}_{hand_label}_{top_name}_{finger_gesture_text}.jpg".replace(" ", "_").replace(":", "")
                    cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                except Exception as e:
                    print(f"Failed to save debug image: {e}")

def process_hands(frame, recognition_result):
    h, w = frame.shape[:2]
    try:
        gestures_list, handedness_list, landmarks_list = extract_lists(recognition_result)
        count = min(len(gestures_list), len(handedness_list), len(landmarks_list))

        left_corner_text = None
        right_corner_text = None
        boost_applied_this_frame = False

        for i in range(count):
            try:
                hand_label = handedness_list[i][0].category_name if handedness_list[i] else "Unknown"
                color = (255, 0, 0) if hand_label == "Left" else (0, 0, 255)

                top_gesture_text = ""
                top_gesture = None
                if gestures_list[i] and len(gestures_list[i]) > 0:
                    top_gesture = gestures_list[i][0]
                    top_gesture_text = f"{top_gesture.category_name} {top_gesture.score:.2f}"

                proto = to_landmark_proto(landmarks_list[i])

                cfg.mp_drawing.draw_landmarks(
                    frame,
                    proto,
                    cfg.mp_hands.HAND_CONNECTIONS,
                    cfg.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=3),
                    cfg.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
                )

                finger_gesture_text, _ = detect_finger_gesture(proto, hand_label)

                _log_gesture_change(hand_label, top_gesture, finger_gesture_text, frame)
                
                boost_applied = select_and_call_func(top_gesture, hand_label, finger_gesture_text)
                boost_applied_this_frame = boost_applied_this_frame or boost_applied
                left_corner_text, right_corner_text = get_labels(top_gesture_text, hand_label, finger_gesture_text, left_corner_text, right_corner_text)

                if should_calculate_angle(top_gesture, finger_gesture_text) and hand_label == cfg.off_hand:
                    degrees = calculate_pointer_angle(proto, hand_label)
                    if degrees is not None:
                        update_mouse_movement(degrees, cfg.cursor_speed)
            except Exception:
                print("Error while processing single hand:")
                traceback.print_exc()

        is_applied_boost(boost_applied_this_frame)
        frame = draw_corner_labels(frame, w, left_corner_text, right_corner_text)
    except Exception:
        print("Error in process_hands:")
        traceback.print_exc()

    return frame