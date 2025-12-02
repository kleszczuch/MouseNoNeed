import mediapipe as mp
import cv2

class config:
    cursor_speed = 10 
    main_hand = "Left"
    default_cursor_speed = cursor_speed
    speed_boost_factor = 2
    speed_boost_active = False
    if main_hand == "Right":
        off_hand = "Left"
    else:
        off_hand = "Right"

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands  
    camera_width = 1280
    camera_height = 720
    last_click_time = 0
    MODEL_FILENAME = "gesture_recognizer.task"
    camera_index = 0  
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2

cfg = config()