from function_library.math_functions import calculate_distance
import time

_GESTURE_DEBOUNCE_SEC = 0.15
_pointer_candidate_since = {}
_two_fingers_candidate_since = {}

_PINCH_DEBOUNCE_SEC = 0.08
_pinch_candidate_since = {}
_pinch_active_until = {}
_PINCH_LOCK_SEC = 0.20

def is_finger_open(tip, mcp, wrist, *, margin: float = 1.10, min_tip_mcp_dist: float = 0.035):
    if tip is None or mcp is None or wrist is None:
        return False
    dist_tip_wrist = calculate_distance(wrist, tip)
    dist_mcp_wrist = calculate_distance(wrist, mcp)
    dist_tip_mcp = calculate_distance(tip, mcp)
    return (dist_tip_wrist > dist_mcp_wrist * margin) and (dist_tip_mcp > min_tip_mcp_dist)

def detect_finger_gesture(proto, hand_label):
    try:
        if len(proto.landmark) <= 12:
            return "", False

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

        now = time.monotonic()
        
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
        
        is_pointer = index_open and (not middle_open) and (not ring_open) and (not pinky_open)
        is_victory = index_open and middle_open and (not ring_open) and (not pinky_open)
        
        allow_pinch = not (is_pointer or is_victory)

        pinch_label = None
        pinch_dist = None
        if allow_pinch and thumb_tip is not None:
            pinch_pairs = [
                ("Index", index_tip),
                ("Middle", middle_tip),
                ("Ring", ring_tip),
                ("Pinky", pinky_tip),
            ]

            for name, tip in pinch_pairs:
                if tip is None:
                    continue
                d = calculate_distance(thumb_tip, tip)
                if d <= 0.030 and (pinch_dist is None or d < pinch_dist):
                    pinch_dist = d
                    pinch_label = f"Thumb+{name}"

        if pinch_label is not None:
            since = _pinch_candidate_since.get(hand_label)
            if since is None:
                _pinch_candidate_since[hand_label] = now
            elif (now - since) >= _PINCH_DEBOUNCE_SEC:
                _pinch_active_until[hand_label] = now + _PINCH_LOCK_SEC
                _pointer_candidate_since.pop(hand_label, None)
                _two_fingers_candidate_since.pop(hand_label, None)
                return pinch_label, False
        else:
            _pinch_candidate_since.pop(hand_label, None)

        if _pinch_active_until.get(hand_label, 0.0) > now:
            return "", False

        two_fingers_candidate = index_open and middle_open and (not ring_open) and (not pinky_open)
        if two_fingers_candidate:
            _pointer_candidate_since.pop(hand_label, None)
            since = _two_fingers_candidate_since.get(hand_label)
            if since is None:
                _two_fingers_candidate_since[hand_label] = now
            elif (now - since) >= _GESTURE_DEBOUNCE_SEC:
                return are_2_fingers_up_or_down(index_tip.y, index_mcp.y), False
        else:
            _two_fingers_candidate_since.pop(hand_label, None)

        pointer_candidate = index_open and (not middle_open) and (not ring_open) and (not pinky_open)
        if pointer_candidate:
            since = _pointer_candidate_since.get(hand_label)
            if since is None:
                _pointer_candidate_since[hand_label] = now
            elif (now - since) >= _GESTURE_DEBOUNCE_SEC:
                return "pointer", False
        else:
            _pointer_candidate_since.pop(hand_label, None)
        return "", False
    except Exception:
        return "", False
    
def are_2_fingers_up_or_down(index_tip, index_mcp):
    if index_tip < index_mcp:
        return "2 fingers: Up"
    else:
        return "2 fingers: Down"
