from configuration.config import cfg
from func_lib.math_functions import is_applied_boost, should_calculate_angle, calculate_pointer_angle
from camera_lib.camera import draw_corner_labels, get_labels, to_landmark_proto, extract_lists
from func_lib.mouse import update_mouse_movement
import traceback
from hand_recognition.predefinied import get_predefined_gesture
from hand_recognition.manual import detect_finger_gesture


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

                finger_gesture_text, boost_applied = detect_finger_gesture(proto, hand_label)
                boost_applied_this_frame = boost_applied_this_frame or boost_applied
                left_corner_text, right_corner_text = get_labels(top_gesture_text, hand_label, finger_gesture_text, left_corner_text, right_corner_text)
                               
                get_predefined_gesture(top_gesture, hand_label)

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