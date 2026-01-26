import json
from pathlib import Path
from configuration.configuration import cfg
from function_library.trigerable_functions import (
    click_func,
    right_click_func,
    update_scrolling,
    apply_speed_boost,
    volume_up,
    volume_down,
    toggle_mute,
    launch_voice_assistant,
    open_on_screen_keyboard,
    next_song,
    previous_song,
    play_pause_music,
    record_key_press,
    press_custom_key,
    minimize_window,
    maximize_window,
    double_click_func,
)

FUNC_FILE = Path(__file__).with_name("function_assigne.json")

def load_func_assignments():
    with FUNC_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
        return {entry["hand"]: entry["functions"][0] for entry in raw}
    
assignments = load_func_assignments()

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
    elif func_name == "right_click_func":
        cfg.last_click_time = right_click_func(cfg.last_click_time)
        return False
    elif func_name == "apply_boost":
        apply_speed_boost()
        return True
    elif func_name == "update_scrolling up":
        update_scrolling(1)
        return False
    elif func_name == "update_scrolling down":
        update_scrolling(-1)
        return False
    elif func_name == "volume_up":
        volume_up()
        return False
    elif func_name == "volume_down":
        volume_down()
        return False
    elif func_name == "toggle_mute":
        toggle_mute()
        return False
    elif func_name == "voice_assistant":
        launch_voice_assistant()
        return False
    elif func_name == "osk":
        open_on_screen_keyboard()
        return False
    elif func_name == "next_song":
        cfg.last_click_time = next_song(cfg.last_click_time)
        return False
    elif func_name == "previous_song":
        cfg.last_click_time = previous_song(cfg.last_click_time)
        return False
    elif func_name == "play_pause_music":
        cfg.last_click_time = play_pause_music(cfg.last_click_time)
        return False
    elif func_name == "double_click_func":
        cfg.last_click_time = double_click_func(cfg.last_click_time)
        return False
    elif func_name == "minimize_window":
        cfg.last_click_time = minimize_window(cfg.last_click_time)
        return False
    elif func_name == "maximize_window":
        cfg.last_click_time = maximize_window(cfg.last_click_time)
        return False
    elif func_name.startswith("custom_hotkey:"):
        hotkey_name = func_name.split(":", 1)[1]
        register_or_execute_custom_hotkey(hotkey_name)
        return False
    else:
        return False


def register_or_execute_custom_hotkey(hotkey_name):
    if hotkey_name in cfg.custom_hotkeys and cfg.custom_hotkeys[hotkey_name]:
        # Key is already registered
        key = cfg.custom_hotkeys[hotkey_name]
        if cfg.debug_mode:
            print(f"Executing registered hotkey '{hotkey_name}': {key}")
        cfg.last_click_time = press_custom_key(key, cfg.last_click_time)
    else:
        # Key is not registered.
        if cfg.debug_mode:
            print(f"Custom hotkey '{hotkey_name}' not found in configuration.")


def _save_custom_hotkeys():
    try:
        config_path = Path(__file__).parent.parent / "configuration.json"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        else:
            config_data = {}
        
        config_data["custom_hotkeys"] = cfg.custom_hotkeys
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        if cfg.debug_mode:
            print("Custom hotkeys saved to configuration.json")
    except Exception as e:
        if cfg.debug_mode:
            print(f"Error saving custom hotkeys: {e}")