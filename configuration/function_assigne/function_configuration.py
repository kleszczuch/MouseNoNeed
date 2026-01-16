import json
from pyparsing import Path
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
        next_song()
        return False
    elif func_name == "previous_song":
        previous_song()
        return False
    elif func_name == "play_pause_music":
        play_pause_music()
        return False
    elif func_name.startswith("custom_hotkey:"):
        # custom_hotkey:hotkey_name
        hotkey_name = func_name.split(":", 1)[1]
        register_or_execute_custom_hotkey(hotkey_name)
        return False
    else:
        return False
    # Add any new functions here as needed


def register_or_execute_custom_hotkey(hotkey_name):
    if hotkey_name in cfg.custom_hotkeys and cfg.custom_hotkeys[hotkey_name]:
        # Klawisz już jest zarejestrowany
        key = cfg.custom_hotkeys[hotkey_name]
        if cfg.debug_mode:
            print(f"Wykonywanie zarejestrowanego hotkey '{hotkey_name}': {key}")
        press_custom_key(key)
    else:
        # Klawisz nie jest zarejestrowany
        if cfg.debug_mode:
            print(f"Rejestracja nowego hotkey '{hotkey_name}'")
        print(f"[Custom Hotkey] Naciśnij klawisz dla '{hotkey_name}'...")
        recorded_key = record_key_press()
        
        if recorded_key:
            cfg.custom_hotkeys[hotkey_name] = recorded_key
            _save_custom_hotkeys()
            if cfg.debug_mode:
                print(f"Hotkey '{hotkey_name}' zarejestrowany jako: {recorded_key}")
            print(f"[Custom Hotkey] '{hotkey_name}' ustawiony na: {recorded_key}")


def _save_custom_hotkeys():
    try:
        config_path = Path("configuration/configuration.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        config_data["custom_hotkeys"] = cfg.custom_hotkeys
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        if cfg.debug_mode:
            print("Custom hotkeys zapisane do configuration.json")
    except Exception as e:
        if cfg.debug_mode:
            print(f"Błąd przy zapisywaniu custom hotkeys: {e}")