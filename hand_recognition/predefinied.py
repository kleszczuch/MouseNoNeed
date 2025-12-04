from config import cfg
from func_lib.functions import click_func

def close_fist_func(hand_label):
    if hand_label == cfg.main_hand:
        cfg.last_click_time = click_func(cfg.last_click_time)
    elif hand_label == cfg.off_hand:
        print("Closed_Fist_off")
def open_palm_func(hand_label):
    if hand_label == cfg.main_hand:
        print("Open_Palm_main")
    elif hand_label == cfg.off_hand:
        print("Open_Palm_off")
def love_you_gesture_func(hand_label):
    if hand_label == cfg.main_hand:
        print("love_you_gesture_main")
    elif hand_label == cfg.off_hand:
        print("love_you_gesture_off")
def thumbs_up_func(hand_label):
    if hand_label == cfg.main_hand:
        print("Thumbs_Up_main")
    elif hand_label == cfg.off_hand:
        print("Thumbs_Up_off")
def thumbs_down_func(hand_label):
    if hand_label == cfg.main_hand:
        print("Thumbs_Down_main")
    elif hand_label == cfg.off_hand:
        print("Thumbs_Down_off")
    

def get_predefined_gesture(top_gesture,hand_label):
    if top_gesture.category_name == "Closed_Fist":
       close_fist_func(hand_label)
    elif top_gesture.category_name == "Open_Palm":
        open_palm_func(hand_label)
    elif top_gesture.category_name == "love_you_gesture":
        love_you_gesture_func(hand_label)
    elif top_gesture.category_name == "Thumbs_Up":
        thumbs_up_func(hand_label)
    elif top_gesture.category_name == "Thumbs_Down":
        thumbs_down_func(hand_label)
    elif top_gesture is None:
        return None
    
