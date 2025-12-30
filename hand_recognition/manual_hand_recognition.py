from function_library.math_functions import calculate_distance

def is_finger_open(tip, mcp, wrist, *, margin: float = 1.10, min_tip_mcp_dist: float = 0.035):
    if tip is None or mcp is None or wrist is None:
        return False
    dist_tip_wrist = calculate_distance(wrist, tip)
    dist_mcp_wrist = calculate_distance(wrist, mcp)
    dist_tip_mcp = calculate_distance(tip, mcp)
    return (dist_tip_wrist > dist_mcp_wrist * margin) and (dist_tip_mcp > min_tip_mcp_dist)


def detect_finger_gesture(proto, hand_label):
    finger_gesture_text = ""
    try:
        boost_applied = False
        if len(proto.landmark) <= 12:
            return finger_gesture_text, False

        wrist = proto.landmark[0]
        thumb_tip = proto.landmark[4]
        thumb_mcp = proto.landmark[2]
        index_tip = proto.landmark[8]
        index_mcp = proto.landmark[5]
        middle_tip = proto.landmark[12]
        middle_mcp = proto.landmark[9]
        ring_tip = proto.landmark[16] if len(proto.landmark) > 16 else None
        ring_mcp = proto.landmark[13] if len(proto.landmark) > 13 else None
        pinky_tip = proto.landmark[20] if len(proto.landmark) > 20 else None
        pinky_mcp = proto.landmark[17] if len(proto.landmark) > 17 else None
        

        thumb_open = is_finger_open(thumb_tip, thumb_mcp, wrist)
        index_open = is_finger_open(index_tip, index_mcp, wrist)
        middle_open = is_finger_open(
            middle_tip,
            middle_mcp,
            wrist,
            margin=1.20,
            min_tip_mcp_dist=0.050,
        )
        ring_open = is_finger_open(ring_tip, ring_mcp, wrist) if ring_tip and ring_mcp else False
        pinky_open = is_finger_open(pinky_tip, pinky_mcp, wrist) if pinky_tip and pinky_mcp else False

        boost_applied = False

        if index_open and middle_open and not ring_open and not pinky_open:
            finger_gesture_text = are_2_fingers_up_or_down(index_tip.y, index_mcp.y)
        elif index_open and not middle_open:
            finger_gesture_text = "pointer"

        return finger_gesture_text, boost_applied
    except Exception:
        return "", False
    
def are_2_fingers_up_or_down(index_tip, index_mcp):
    if index_tip < index_mcp:
        finger_gesture_text = "2 fingers: Up"
    else:
        finger_gesture_text = "2 fingers: Down"
    return finger_gesture_text
