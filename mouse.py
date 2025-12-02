import math
import pyautogui
import time

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  #No delay between actions
remainder_x = 0.0
remainder_y = 0.0

def update_mouse_movement(angle_degrees, speed_px_per_sec):
    global remainder_x, remainder_y

    # 1. Convert angle to radians
    angle_radians = math.radians(angle_degrees)

    # 2. Calculate fractional X and Y components
    dx_float = speed_px_per_sec * math.cos(angle_radians)
    dy_float = -speed_px_per_sec * math.sin(angle_radians) # Minus because Y increases downward
    # 3. Add fractions of the movement 
    remainder_x += dx_float
    remainder_y += dy_float

    # 4. Check if we have accumulated a full pixel (integer)
    move_int_x = int(remainder_x)
    move_int_y = int(remainder_y)

    # 5. If we have a full pixel, move the mouse
    if move_int_x != 0 or move_int_y != 0:
        pyautogui.moveRel(move_int_x, move_int_y)
        remainder_x -= move_int_x
        remainder_y -= move_int_y

def click_func(last_click_time):
    current_time = time.time()
    print(f"Time since last click: {current_time - last_click_time:.2f} seconds")
    if current_time - last_click_time > 1:
        pyautogui.click()  
        return current_time
    return last_click_time