import math
import os
import time
import tempfile
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
from mediapipe.framework.formats import landmark_pb2

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands  

camera_width = 1280
camera_height = 720

MODEL_FILENAME = "gesture_recognizer.task"

def convert_hand_landmarks_proto_to_drawable(hand_landmarks_proto):
    return hand_landmarks_proto

def main():
    if mp_tasks_python is None or mp_tasks_vision is None:
        print("Mediapipe Tasks API (GestureRecognizer) is not available in this mediapipe installation.")
        print("Install mediapipe with Tasks support or use an environment compatible with MediaPipe documentation.")
        return

    base_options = mp_tasks_python.BaseOptions(model_asset_path=MODEL_FILENAME)
    options = mp_tasks_vision.GestureRecognizerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=mp_tasks_vision.RunningMode.VIDEO
        )
    recognizer = mp_tasks_vision.GestureRecognizer.create_from_options(options)

    camera_index = 0  
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Unable to open camera.")
        return
 
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera {camera_index}: {actual_w}x{actual_h}")
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
                # prefer in-memory factory from mediapipe
                mp_image = mp.Image.create_from_array(image_rgb)
            except Exception:
                # fallback: write temp file and create from file (slower)
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
                for i in range(count):
                    # Handedness: "Left" / "Right" 
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
                    mp_drawing.draw_landmarks(
                        frame,
                        proto,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=3),
                        mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
                    )

                
                    label = f"{hand_label}: {top_gesture_text}" if top_gesture_text else f"{hand_label}: -"
                    if hand_label == "Left":
                        left_corner_text = label
                    elif hand_label == "Right":
                        right_corner_text = label
                    if top_gesture and top_gesture.category_name == "Pointing_Up": # To change
                        try:
                            if len(proto.landmark) > 8:
                                p5 = proto.landmark[5]
                                p8 = proto.landmark[8]
                                dx = p8.x - p5.x
                                dy_math = (p5.y - p8.y)
                                theta = math.degrees(math.atan2(dy_math, dx))
                                theta = (theta + 360.0) % 360.0
                                degrees = (180.0 - theta) % 360.0
                                # Obraz jest lustrzany (cv2.flip(...,1)), więc odwracamy lewo/prawo
                                degrees_mirrored = (180.0 - degrees) % 360.0
                                print(f"  -> ACTION ({hand_label}): 'Pointing_Up' tilt: {degrees_mirrored:.2f}° (L=0,U=90,R=180,D=270, mirrored)") # DEBUG
                            else:
                                print("Required landmarks for angle calculation are missing (need 5 and 8).") # DEBUG
                        except Exception as e:
                            print(f"Error calculating angle: {e}") # DEBUG


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