
import time
import pyautogui

def click_func(last_click_time):
    current_time = time.time()
    print(f"Time since last click: {current_time - last_click_time:.2f} seconds")
    if current_time - last_click_time > 1:
        pyautogui.click()  
        return current_time
    return last_click_time