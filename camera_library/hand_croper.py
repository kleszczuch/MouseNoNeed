class HandCropper:
    def __init__(self, output_width, output_height, smoothing_factor=0.1):
        self.output_width = output_width
        self.output_height = output_height
        self.smoothing_factor = smoothing_factor
        self.current_crop_x = None
        self.current_crop_y = None

    def _init_if_needed(self, frame_width, frame_height):
        if self.current_crop_x is None or self.current_crop_y is None:
            self.current_crop_x = (frame_width - self.output_width) // 2
            self.current_crop_y = (frame_height - self.output_height) // 2

    def crop(self, frame, multi_hand_landmarks):
        h, w = frame.shape[:2]
        self._init_if_needed(w, h)

        target_center_x = w // 2
        target_center_y = h // 2
        hand_found = False

        if multi_hand_landmarks:
            hand_found = True
            centers = []
            for hand_landmarks in multi_hand_landmarks:
                wrist = hand_landmarks[0]
                middle_tip = hand_landmarks[12]
                cx = int((wrist.x + middle_tip.x) / 2 * w)
                cx = w - cx
                cy = int((wrist.y + middle_tip.y) / 2 * h)
                centers.append((cx, cy))
            if len(centers) == 1:
                target_center_x, target_center_y = centers[0]
            else:
                (x1, y1), (x2, y2) = centers[0], centers[1]
                target_center_x = (x1 + x2) // 2
                target_center_y = (y1 + y2) // 2

        if hand_found:
            target_crop_x = target_center_x - (self.output_width // 2)
            target_crop_y = target_center_y - (self.output_height // 2)
        else:
            target_crop_x = (w - self.output_width) // 2
            target_crop_y = (h - self.output_height) // 2

        self.current_crop_x = self.current_crop_x + (target_crop_x - self.current_crop_x) * self.smoothing_factor
        self.current_crop_y = self.current_crop_y + (target_crop_y - self.current_crop_y) * self.smoothing_factor

        x1 = int(max(0, min(self.current_crop_x, w - self.output_width)))
        y1 = int(max(0, min(self.current_crop_y, h - self.output_height)))
        x2 = x1 + self.output_width
        y2 = y1 + self.output_height

        return frame[y1:y2, x1:x2]