import math
from configuration.config import cfg

def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def should_calculate_angle(top_gesture, finger_gesture_text):
    if top_gesture and top_gesture.category_name == "Pointing_Up":
        return True
    if finger_gesture_text and "pointer" in finger_gesture_text:
        return True
    return False


def calculate_pointer_angle(proto, hand_label):
    try:
        if len(proto.landmark) <= 8:
            print("Required landmarks for angle calculation are missing (need 5 and 8).")
            return None

        p5 = proto.landmark[5]
        p8 = proto.landmark[8]
        dx = p8.x - p5.x
        dy_math = p5.y - p8.y
        theta = math.degrees(math.atan2(dy_math, dx))
        theta = (theta + 360.0) % 360.0
        degrees = (180.0 - theta) % 360.0
        degrees_mirrored = (180.0 - degrees) % 360.0
        #print(f"  -> ACTION ({hand_label}): 'pointer' tilt: {degrees_mirrored:.2f}° mirrored)")
        return degrees
    except Exception as e:
        print(f"Error calculating angle: {e}")
        return None

def is_applied_boost(boost_applied_this_frame):
    #print("RESET BOOST:", boost_applied_this_frame, cfg.speed_boost_active)    
    if not boost_applied_this_frame and cfg.speed_boost_active:
        cfg.cursor_speed = cfg.default_cursor_speed
        cfg.scroll_speed = cfg.default_scroll_speed
        cfg.speed_boost_active = False

def apply_speed_boost():
    #print("APPLY BOOST:", cfg.cursor_speed, cfg.scroll_speed)
    cfg.cursor_speed = int(cfg.default_cursor_speed * cfg.speed_boost_factor)
    cfg.scroll_speed = int(cfg.default_scroll_speed * cfg.speed_boost_factor)
    cfg.speed_boost_active = True