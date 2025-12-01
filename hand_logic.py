import cv2
import mediapipe as mp
import math

class HandRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True, 
            max_num_hands=1, 
            min_detection_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect_move(self, image_bytes):
        # Convert byte array to image
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return "Unknown"

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        if not results.multi_hand_landmarks:
            return "None" # Không thấy tay

        # Lấy landmarks của bàn tay đầu tiên
        lm_list = []
        hand_lms = results.multi_hand_landmarks[0]
        for id, lm in enumerate(hand_lms.landmark):
            h, w, c = img.shape
            lm_list.append((int(lm.x * w), int(lm.y * h)))

        return self._classify_gesture(lm_list)

    def _classify_gesture(self, lm_list):
        # Logic đơn giản để phân loại Kéo Búa Bao
        if not lm_list: return "None"

        # Các đầu ngón tay: 8 (Trỏ), 12 (Giữa), 16 (Nhẫn), 20 (Út)
        # Búa: Tất cả ngón gập
        # Bao: Tất cả ngón mở
        # Kéo: Ngón trỏ (8) và giữa (12) mở
        
        # Kiểm tra ngón mở (trừ ngón cái - id 4 phức tạp hơn chút)
        fingers = []
        
        # Ngón cái (kiểm tra trục x tùy tay trái phải, tạm thời bỏ qua để đơn giản hoặc check đơn giản)
        # Check 4 ngón còn lại (y của đầu ngón < y của khớp dưới)
        tips = [8, 12, 16, 20]
        for tip in tips:
            if lm_list[tip][1] < lm_list[tip - 2][1]: # Đang mở
                fingers.append(1)
            else:
                fingers.append(0)

        total_fingers = fingers.count(1)

        # Logic phân loại
        if total_fingers == 0:
            return "Rock" # Búa
        elif total_fingers == 4 or total_fingers == 3: # Đôi khi ngón cái không chuẩn
            return "Paper" # Bao
        elif total_fingers == 2 and fingers[0] == 1 and fingers[1] == 1:
            return "Scissors" # Kéo
        elif total_fingers == 5:
             return "Paper"
        
        return "Unknown"