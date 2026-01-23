import mediapipe as mp
import cv2
import json
import os

from dataclasses import dataclass, field

current_dir = os.path.dirname(os.path.abspath(__file__))
configuration_file_path = os.path.join(current_dir, 'configuration.json')
try:
    with open(configuration_file_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except:
    settings = {}

@dataclass
class Config:
    cursor_speed: int = settings.get("cursor_speed", 20)
    _main_hand: str = field(default=settings.get("main_hand", "Right"), init=False)
    default_cursor_speed: int = settings.get("default_cursor_speed", 20)
    speed_boost_factor: float = settings.get("speed_boost_factor", 2.0)
    scroll_speed: int = settings.get("scroll_speed", 25)
    default_scroll_speed: int = settings.get("default_scroll_speed", 25)
    speed_boost_active: bool = settings.get("speed_boost_active", False)
    camera_width_default: int = settings.get("camera_width_default", 640)
    camera_height_default: int = settings.get("camera_height_default", 480)
    camera_width_crop: int = settings.get("camera_width_crop", 400)
    camera_height_crop: int = settings.get("camera_height_crop", 300)
    last_click_time: float = settings.get("last_click_time", 0.0)
    camera_index: int = settings.get("camera_index", 0)
    font_scale: float = settings.get("font_scale", 1.0)
    thickness: int = settings.get("thickness", 2)
    debug_mode: bool = settings.get("debug_mode", False)
    custom_hotkeys: dict = field(default_factory=lambda: settings.get("custom_hotkeys", {}))
    
    MODEL_FILENAME: str = os.path.join(current_dir, "gesture_recognizer.task")
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    off_hand: str = field(init=False)

    def __post_init__(self):
        self._main_hand = settings.get("main_hand", "Right")
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