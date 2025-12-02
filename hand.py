from mouse import click_func
from config import cfg
from math_functions import calculate_distance, should_calculate_angle, calculate_pointer_angle
from camera import draw_corner_labels, to_landmark_proto, extract_lists
from scroll import update_scrolling
from mouse import update_mouse_movement
import traceback

def maybe_click(top_gesture, hand_label):
    if not top_gesture:
        return
    try:
        if top_gesture.category_name == "Closed_Fist" and hand_label == cfg.main_hand:
            cfg.last_click_time = click_func(cfg.last_click_time)
    except Exception as e:
        print(f"Error while invoking click_func: {e}")

def is_finger_open(tip, mcp, wrist, *, margin: float = 1.10, min_tip_mcp_dist: float = 0.035):
    if tip is None or mcp is None or wrist is None:
        return False
    dist_tip_wrist = calculate_distance(wrist, tip)
    dist_mcp_wrist = calculate_distance(wrist, mcp)
    dist_tip_mcp = calculate_distance(tip, mcp)
    return (dist_tip_wrist > dist_mcp_wrist * margin) and (dist_tip_mcp > min_tip_mcp_dist)

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

                label = f"{hand_label}: {top_gesture_text}" if top_gesture_text else f"{hand_label}: -"
                if finger_gesture_text:
                    label = f"{label} | {finger_gesture_text}"
                
                if hand_label == "Left":
                    left_corner_text = label
                elif hand_label == "Right":
                    right_corner_text = label
                #Place for diff pre-defined actions based on recognized gestures
                maybe_click(top_gesture, hand_label)

                if should_calculate_angle(top_gesture, finger_gesture_text) and hand_label == cfg.second_hand:
                    degrees = calculate_pointer_angle(proto, hand_label)
                    if degrees is not None:
                        update_mouse_movement(degrees, cfg.cursor_speed)
            except Exception:
                print("Error while processing single hand:")
                traceback.print_exc()

        if not boost_applied_this_frame and cfg.speed_boost_active:
            cfg.cursor_speed = cfg.default_cursor_speed
            cfg.speed_boost_active = False

        frame = draw_corner_labels(frame, w, left_corner_text, right_corner_text)
    except Exception:
        print("Error in process_hands:")
        traceback.print_exc()

    return frame

def detect_finger_gesture(proto, hand_label):
    finger_gesture_text = ""
    try:
        if len(proto.landmark) <= 12:
            return finger_gesture_text, False

        wrist = proto.landmark[0]
        index_tip = proto.landmark[8]
        index_mcp = proto.landmark[5]
        middle_tip = proto.landmark[12]
        middle_mcp = proto.landmark[9]
        ring_tip = proto.landmark[16] if len(proto.landmark) > 16 else None
        ring_mcp = proto.landmark[13] if len(proto.landmark) > 13 else None
        pinky_tip = proto.landmark[20] if len(proto.landmark) > 20 else None
        pinky_mcp = proto.landmark[17] if len(proto.landmark) > 17 else None

        index_open = is_finger_open(index_tip, index_mcp, wrist)
        middle_open = is_finger_open(
            middle_tip,
            middle_mcp,
            wrist,
            margin=1.20,
            min_tip_mcp_dist=0.050,
        )
        ring_open = is_finger_open(ring_tip, ring_mcp, wrist) if ring_tip and ring_mcp else False
        pinky_open = is_finger_open(pinky_tip, pinky_mcp, wrist) if pinky_tip and pinky_mcp else False

        boost_applied = False

        if index_open and middle_open and not ring_open and not pinky_open:
            if index_tip.y < index_mcp.y:
                finger_gesture_text = "2 fingers: UP"
                if hand_label == cfg.second_hand:
                    update_scrolling(5)
                elif hand_label == cfg.main_hand:
                    if not cfg.speed_boost_active:
                        cfg.cursor_speed = int(cfg.default_cursor_speed * cfg.speed_boost_factor)
                        cfg.speed_boost_active = True
                    boost_applied = True
            else:
                finger_gesture_text = "2 fingers: DOWN"
                if hand_label == cfg.second_hand:
                    update_scrolling(-5)
        elif index_open and not middle_open:
            finger_gesture_text = "pointer"

        return finger_gesture_text, boost_applied
    except Exception:
        return "", False