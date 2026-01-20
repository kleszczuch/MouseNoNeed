import mediapipe as mp
import cv2
import json

from dataclasses import dataclass, field

configuration_file_path = 'configuration/configuration.json'
settings = json.load(open(configuration_file_path))

@dataclass
class Config:
    cursor_speed: int = settings["cursor_speed"]
    _main_hand: str = field(default=settings["main_hand"], init=False)
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
    custom_hotkeys: dict = field(default_factory=lambda: settings.get("custom_hotkeys", {}))
    
    MODEL_FILENAME: str = "configuration/gesture_recognizer.task"
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    off_hand: str = field(init=False)

    def __post_init__(self):
        self._main_hand = settings["main_hand"]
        self._update_off_hand()
    
    @property
    def main_hand(self):
        return self._main_hand
    
    @main_hand.setter
    def main_hand(self, value):
        self._main_hand = value
        self._update_off_hand()
    
    def _update_off_hand(self):
        if self._main_hand == "Right":
            self.off_hand = "Left"
        else:
            self.off_hand = "Right"

cfg = Config()