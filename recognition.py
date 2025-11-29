import math
import os
import time
import tempfile
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
from mediapipe.framework.formats import landmark_pb2
from click import click_func
from mouse import update_mouse_movement
from scroll import update_scrolling

class config:
    cursor_speed = 10 
    main_hand = "Right"
    default_cursor_speed = cursor_speed
    speed_boost_factor = 2
    speed_boost_active = False
    if main_hand == "Right":
        mouse_movement_hand = "Left"
    else:
        mouse_movement_hand = "Right"

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands  
    camera_width = 1280
    camera_height = 720
    last_click_time = 0
    MODEL_FILENAME = "gesture_recognizer.task"
    camera_index = 0  


config = config()

def convert_hand_landmarks_proto_to_drawable(hand_landmarks_proto):
    return hand_landmarks_proto

def calculate_distance(p1, p2): 
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def is_finger_open(tip, mcp, wrist, *, margin: float = 1.10, min_tip_mcp_dist: float = 0.035):
    if tip is None or mcp is None or wrist is None:
        return False
    dist_tip_wrist = calculate_distance(wrist, tip)
    dist_mcp_wrist = calculate_distance(wrist, mcp)
    dist_tip_mcp = calculate_distance(tip, mcp)
    return (dist_tip_wrist > dist_mcp_wrist * margin) and (dist_tip_mcp > min_tip_mcp_dist)

def main():
    if mp_tasks_python is None or mp_tasks_vision is None:
        print("No MediaPipe Tasks API (GestureRecognizer) available.")
        return

    base_options = mp_tasks_python.BaseOptions(model_asset_path=config.MODEL_FILENAME)
    options = mp_tasks_vision.GestureRecognizerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=mp_tasks_vision.RunningMode.VIDEO
        )
    recognizer = mp_tasks_vision.GestureRecognizer.create_from_options(options)

    cap = cv2.VideoCapture(config.camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Unable to open camera.")
        return
 
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera_height)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera {config.camera_index}: {actual_w}x{actual_h}")
    cv2.setUseOptimized(True)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # convert BGR->RGB
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Create MediaPipe Tasks Image. Try in-memory; if not available fallback to temp file.
            mp_image = None
            try:
                mp_image = mp.Image.create_from_array(image_rgb)
            except Exception:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    cv2.imwrite(tmp.name, frame)
                    tmp_path = tmp.name
                try:
                    mp_image = mp.Image.create_from_file(tmp_path)
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            # Run recognition (IMAGE mode)
            timestamp_ms = int(time.time() * 1000)
            recognition_result = recognizer.recognize_for_video(mp_image, timestamp_ms)
            h, w = frame.shape[:2]
            # recognition_result.gestures is a list of lists; take top for first hand if present
            try:
                gestures_list = recognition_result.gestures or []
                handedness_list = recognition_result.handedness or []
                landmarks_list = recognition_result.hand_landmarks or []
                if recognition_result.gestures and len(recognition_result.gestures) > 0 and len(recognition_result.gestures[0]) > 0:
                    top = recognition_result.gestures[0][0]
            except Exception:
                pass
            # Draw hand landmarks (if present)
            try:
                gestures_list = recognition_result.gestures or []
                handedness_list = recognition_result.handedness or []
                landmarks_list = recognition_result.hand_landmarks or []

                count = min(len(gestures_list), len(handedness_list), len(landmarks_list))
                # ensure corner labels exist even if no hands detected in this frame
                left_corner_text = None
                right_corner_text = None
                # track whether any hand applied a speed boost this frame
                boost_applied_this_frame = False
                for i in range(count):
                    hand_label = handedness_list[i][0].category_name if handedness_list[i] else "Unknown"

                    # Color: left – blue (BGR), right – red
                    color = (255, 0, 0) if hand_label == "Left" else (0, 0, 255)

                    # Top gesture (if present) 
                    top_gesture_text = ""
                    top_gesture = None
                    if gestures_list[i] and len(gestures_list[i]) > 0:
                        top_gesture = gestures_list[i][0]
                        top_gesture_text = f"{top_gesture.category_name} {top_gesture.score:.2f}"

                    # Prepare proto for drawing
                    hand_lms = landmarks_list[i]
                    if isinstance(hand_lms, landmark_pb2.NormalizedLandmarkList):
                        proto = hand_lms
                    else:
                        proto = landmark_pb2.NormalizedLandmarkList()
                        for idx, lm in enumerate(hand_lms):
                            proto.landmark.add(x=lm.x, y=lm.y, z=getattr(lm, "z", 0.0))

                    # Draw landmarks
                    config.mp_drawing.draw_landmarks(
                        frame,
                        proto,
                        config.mp_hands.HAND_CONNECTIONS,
                        config.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=3),
                        config.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
                    )
                    finger_gesture_text = ""
                    try:
                        if len(proto.landmark) > 12:
                            wrist = proto.landmark[0]
                            index_tip = proto.landmark[8]
                            index_mcp = proto.landmark[5]
                            middle_tip = proto.landmark[12]
                            middle_mcp = proto.landmark[9]
                            ring_tip = proto.landmark[16] if len(proto.landmark) > 16 else None
                            ring_mcp = proto.landmark[13] if len(proto.landmark) > 13 else None
                            pinky_tip = proto.landmark[20] if len(proto.landmark) > 20 else None
                            pinky_mcp = proto.landmark[17] if len(proto.landmark) > 17 else None

                            # Index detection: standard sensitivity
                            index_open = is_finger_open(index_tip, index_mcp, wrist)
                            # Middle detection: stricter to avoid accidental 2-finger when only index is shown
                            middle_open = is_finger_open(
                                middle_tip, middle_mcp, wrist, margin=1.20, min_tip_mcp_dist=0.050
                            )
                            ring_open = is_finger_open(ring_tip, ring_mcp, wrist) if ring_tip and ring_mcp else False
                            pinky_open = is_finger_open(pinky_tip, pinky_mcp, wrist) if pinky_tip and pinky_mcp else False

                            # Run detection unconditionally (independent from model's top gesture)
                            # 2 fingers: index + middle open (require ring & pinky closed to reduce false positives)
                            if index_open and middle_open and not ring_open and not pinky_open:
                                # determine up/down by comparing tip.y and mcp.y (image coords)
                                if index_tip.y < index_mcp.y:
                                    finger_gesture_text = "2 fingers: UP"
                                    if hand_label == "Left":
                                        update_scrolling(5)
                                    elif hand_label == "Right":
                                        # apply a single boost while gesture is present; avoid loops
                                        if not config.speed_boost_active:
                                            config.cursor_speed = int(config.default_cursor_speed * config.speed_boost_factor)
                                            config.speed_boost_active = True
                                        boost_applied_this_frame = True
                                else:
                                    finger_gesture_text = "2 fingers: DOWN"
                                    if hand_label == "Left":
                                        update_scrolling(-5) 
                            # 1 finger: only index open (middle closed)
                            elif index_open and not middle_open:
                                finger_gesture_text = "pointer"
                    except Exception:
                        # on any error keep finger_gesture_text empty
                        finger_gesture_text = ""

                    label = f"{hand_label}: {top_gesture_text}" if top_gesture_text else f"{hand_label}: -"
                    if finger_gesture_text:
                        label = f"{label} | {finger_gesture_text}"
                    if hand_label == "Left":
                        left_corner_text = label
                    elif hand_label == "Right":
                        right_corner_text = label
                        try:
                            if top_gesture and top_gesture.category_name == "Closed_Fist" and hand_label == config.main_hand:
                                config.last_click_time = click_func(config.last_click_time)
                        except Exception as e:
                            print(f"Error while invoking click_func: {e}")
                    should_calc_angle = False
                    if top_gesture and top_gesture.category_name == "Pointing_Up":
                        should_calc_angle = True
                    if finger_gesture_text and "pointer" in finger_gesture_text:
                        should_calc_angle = True

                    if should_calc_angle:
                        try:
                            if len(proto.landmark) > 8:
                                p5 = proto.landmark[5]
                                p8 = proto.landmark[8]
                                dx = p8.x - p5.x
                                dy_math = (p5.y - p8.y)
                                theta = math.degrees(math.atan2(dy_math, dx))
                                theta = (theta + 360.0) % 360.0
                                degrees = (180.0 - theta) % 360.0
                                # The image is mirrored (cv2.flip(...,1)), so we reverse left/right
                                degrees_mirrored = (180.0 - degrees) % 360.0
                                print(f"  -> ACTION ({hand_label}): 'pointer' tilt: {degrees_mirrored:.2f}° mirrored)") # DEBUG
                            else:
                                print("Required landmarks for angle calculation are missing (need 5 and 8).") # DEBUG
                        except Exception as e:
                            print(f"Error calculating angle: {e}") # DEBUG
                        if hand_label == config.mouse_movement_hand:
                            update_mouse_movement(degrees, config.cursor_speed)
                # if no hand applied boost this frame but boost is active, reset to default
                if not boost_applied_this_frame and config.speed_boost_active:
                    config.cursor_speed = config.default_cursor_speed
                    config.speed_boost_active = False

                frame = cv2.flip(frame, 1)
                # Draw labels only in corners
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                thickness = 2
                # Top left
                if left_corner_text:
                    cv2.putText(frame, left_corner_text, (10, 30), font, font_scale, (255, 0, 0), thickness, cv2.LINE_AA)
                # Top right (right-aligned)
                if right_corner_text:
                    (tw, th), _ = cv2.getTextSize(right_corner_text, font, font_scale, thickness)
                    cv2.putText(frame, right_corner_text, (w - tw - 10, 30), font, font_scale, (0, 0, 255), thickness, cv2.LINE_AA)
            except Exception:
                # drawing failure shouldn't crash the loop
                pass
            cv2.imshow("Gesture Recognizer - press q to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()