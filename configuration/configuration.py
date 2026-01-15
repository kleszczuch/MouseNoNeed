import mediapipe as mp
import cv2
import json

from dataclasses import dataclass, field

configuration_file_path = 'configuration/configuration.json'
settings = json.load(open(configuration_file_path))

@dataclass
class Config:
    cursor_speed: int = int(settings["cursor_speed"])
    main_hand: str = settings["main_hand"]
    default_cursor_speed: int = settings["default_cursor_speed"]
    speed_boost_factor: float = settings["speed_boost_factor"]
    scroll_speed: int = settings["scroll_speed"]
    default_scroll_speed: int = settings["default_scroll_speed"]
    speed_boost_active: bool = settings["speed_boost_active"]
    camera_width_default: int = settings["camera_width_default"]
    camera_height_default: int = settings["camera_height_default"]
    camera_width_crop: int = settings["camera_width_crop"]
    camera_height_crop: int = settings["camera_height_crop"]
    last_click_time: float = settings["last_click_time"]
    camera_index: int = settings["camera_index"]
    font_scale: float = settings["font_scale"]
    thickness: int = settings["thickness"]
    debug_mode: bool = settings.get("debug_mode", False)

    custom_key: str = settings.get("custom_key", "space")

    MODEL_FILENAME: str = "configuration/gesture_recognizer.task"
    font: int = cv2.FONT_HERSHEY_SIMPLEX

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    off_hand: str = field(init=False)

    def __post_init__(self):
        if self.main_hand == "Right":
            self.off_hand = "Left"
        else:
            self.off_hand = "Right"

cfg = Config()