import pyautogui

scroll_remainder = 0.0

def update_scrolling(speed_clicks_per_sec):
    global scroll_remainder
    # add a fraction of a scroll based on speed
    step = speed_clicks_per_sec
    scroll_remainder += step

    # check if we have a full scroll unit
    scroll_int = int(scroll_remainder)
    if scroll_int != 0:
        pyautogui.scroll(scroll_int * 10) 
        
        # Subtract what we've used
        scroll_remainder -= scroll_int