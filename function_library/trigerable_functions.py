import time
import pyautogui
from configuration.configuration import cfg
import math

# PyAutoGUI configuration
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

remainder_x = 0.0
remainder_y = 0.0
scroll_remainder = 0.0

def is_applied_boost(boost_applied_this_frame):
    if cfg.debug_mode:
        print("RESET BOOST:", boost_applied_this_frame, cfg.speed_boost_active)    
    if not boost_applied_this_frame and cfg.speed_boost_active:
        cfg.cursor_speed = cfg.default_cursor_speed
        cfg.scroll_speed = cfg.default_scroll_speed
        cfg.speed_boost_active = False

def apply_speed_boost():
    if cfg.debug_mode:
        print("APPLY BOOST:", cfg.cursor_speed, cfg.scroll_speed)
    cfg.cursor_speed = int(cfg.default_cursor_speed * cfg.speed_boost_factor)
    cfg.scroll_speed = int(cfg.default_scroll_speed * cfg.speed_boost_factor)
    cfg.speed_boost_active = True

def click_func(last_click_time):
    current_time = time.time()
    if cfg.debug_mode:
        print(f"Time since last click: {current_time - last_click_time:.2f} seconds")
    if current_time - last_click_time > 1:
        pyautogui.click()  
    return last_click_time

def update_scrolling(direction=1):
    global scroll_remainder
    step = cfg.scroll_speed if direction > 0 else -cfg.scroll_speed 
    scroll_remainder += step
    scroll_int = int(scroll_remainder)
    if scroll_int != 0:
        pyautogui.scroll(scroll_int * 10) 
        scroll_remainder -= scroll_int


def update_mouse_movement(angle_degrees, speed_px_per_sec):
    global remainder_x, remainder_y
    angle_radians = math.radians(angle_degrees)
    dx_float = speed_px_per_sec * math.cos(angle_radians)
    dy_float = -speed_px_per_sec * math.sin(angle_radians) 
    remainder_x += dx_float
    remainder_y += dy_float
    move_int_x = int(remainder_x)
    move_int_y = int(remainder_y)
    if move_int_x != 0 or move_int_y != 0:
        pyautogui.moveRel(move_int_x, move_int_y)
        remainder_x -= move_int_x
        remainder_y -= move_int_y