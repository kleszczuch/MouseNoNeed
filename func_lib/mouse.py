import math
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  
remainder_x = 0.0
remainder_y = 0.0

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

