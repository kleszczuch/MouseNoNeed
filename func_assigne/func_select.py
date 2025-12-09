from configuration.config import cfg
from func_assigne.func_import import assignments
from func_lib.functions import click_func, update_scrolling
from func_lib.math_functions import apply_speed_boost


def _resolve_hand_key(hand_label):
    if hand_label == cfg.main_hand:
        return "Main"
    if hand_label == cfg.off_hand:
        return "Secondary"
    return None


def select_and_call_func(gesture, hand_label, finger_gesture_text=""):
    hand_key = _resolve_hand_key(hand_label)
    if hand_key is None:
        return False

    gesture_key = finger_gesture_text or (getattr(gesture, "category_name", "") if gesture else "")
    if not gesture_key:
        return False

    hand_mapping = assignments.get(hand_key, {})
    func_name = hand_mapping.get(gesture_key)
    if not func_name or func_name == "None":
        return False

    return call_function(func_name)


def call_function(func_name):
    if func_name == "click_func":
        cfg.last_click_time = click_func(cfg.last_click_time)
        return False
    elif func_name == "apply_boost":
        apply_speed_boost()
        return True
    elif func_name == "update_scrolling(1)":
        update_scrolling(1)
        return False
    elif func_name == "update_scrolling(-1)":
        update_scrolling(-1)
        return False
    else:
        return False
    