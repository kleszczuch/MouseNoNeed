import config as cfg
from functions.mouse import click_func
from config import cfg

def get_gesture_name(top_gesture,hand_label):
    if top_gesture.category_name == "Close_Fist":
       close_fist_func(hand_label)
    elif top_gesture.category_name == "Open_Palm":
        open_palm_func()
    elif top_gesture.category_name == "love_you_gesture":
        love_you_gesture_func()
    elif top_gesture.category_name == "Thumbs_Up":
        thumbs_up_func()
    elif top_gesture.category_name == "Thumbs_Down":
        thumbs_down_func()
    elif top_gesture is None:
        return None
    
    def close_fist_func(hand_label):
        if hand_label == cfg.main_hand:
            cfg.last_click_time = click_func(cfg.last_click_time)
        elif hand_label == cfg.off_hand:
            return "Close_Fist_off"
    def open_palm_func():
        if hand_label == cfg.main_hand:
            return "Open_Palm_main"
        elif hand_label == cfg.off_hand:
            return "Open_Palm_off"
    def love_you_gesture_func():
        if hand_label == cfg.main_hand:
            return "love_you_gesture_main"
        elif hand_label == cfg.off_hand:
            return "love_you_gesture_off"
    def thumbs_up_func():
        if hand_label == cfg.main_hand:
            return "Thumbs_Up_main"
        elif hand_label == cfg.off_hand:
            return "Thumbs_Up_off"
    def thumbs_down_func():
        if hand_label == cfg.main_hand:
            return "Thumbs_Down_main"
        elif hand_label == cfg.off_hand:
            return "Thumbs_Down_off"
    