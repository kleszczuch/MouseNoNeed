import mediapipe as mp
import cv2
import json

configuration_file_path = 'configuration/config.json'
settings = json.load(open(configuration_file_path))

class config:
    cursor_speed = settings["cursor_speed"]
    main_hand = settings["main_hand"]
    default_cursor_speed = settings["default_cursor_speed"]
    speed_boost_factor = settings["speed_boost_factor"]
    scroll_speed = settings["scroll_speed"]
    default_scroll_speed = settings["default_scroll_speed"]
    speed_boost_active = settings["speed_boost_active"] 
    camera_width_default = settings["camera_width_default"]
    camera_height_default = settings["camera_height_default"]
    camera_width_crop = settings["camera_width_crop"]
    camera_height_crop = settings["camera_height_crop"]
    last_click_time = settings["last_click_time"]
    camera_index = settings["camera_index"]  
    font_scale = settings["font_scale"]
    thickness = settings["thickness"]
    
    
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    MODEL_FILENAME = "configuration/gesture_recognizer.task"
    font = cv2.FONT_HERSHEY_SIMPLEX


    if main_hand == "Right":
        off_hand = "Left"
    else:
        off_hand = "Right"

cfg = config()