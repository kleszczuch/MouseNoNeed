import time
import pyautogui
from configuration.config import cfg

def click_func(last_click_time):
    current_time = time.time()
    #print(f"Time since last click: {current_time - last_click_time:.2f} seconds")
    if current_time - last_click_time > 1:
        pyautogui.click()  
        return current_time
    return last_click_time

def update_scrolling(direction=1):
    global scroll_remainder
    scroll_remainder = 0.0
    step = cfg.scroll_speed if direction > 0 else -cfg.scroll_speed 
    scroll_remainder += step
    scroll_int = int(scroll_remainder)
    if scroll_int != 0:
        pyautogui.scroll(scroll_int * 10) 
        scroll_remainder -= scroll_int