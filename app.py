from flask import Flask, render_template, request, jsonify
import base64
import cv2
import numpy as np
import mediapipe as mp
import random

app = Flask(__name__)

# ====== Mediapipe Setup (Server-side AI) ======
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
)


def decode_image(data_uri: str):
    """
    Decode base64 image from Data URL (data:image/jpeg;base64,....) to OpenCV BGR image.
    """
    if not data_uri:
        return None
    if ',' in data_uri:
        _, encoded = data_uri.split(',', 1)
    else:
        encoded = data_uri
    img_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def get_finger_states(landmarks):
    """
    Determine if fingers (index, middle, ring, pinky) are extended based on y-coordinate.
    landmarks: list of 21 mediapipe landmarks.
    Returns dict: {'index': bool, 'middle': bool, 'ring': bool, 'pinky': bool}
    """
    finger_tips = {
        "index": 8,
        "middle": 12,
        "ring": 16,
        "pinky": 20
    }
    finger_pips = {
        "index": 6,
        "middle": 10,
        "ring": 14,
        "pinky": 18
    }
    states = {}
    for finger in finger_tips:
        tip_id = finger_tips[finger]
        pip_id = finger_pips[finger]
        tip_y = landmarks[tip_id].y
        pip_y = landmarks[pip_id].y
        # y nhỏ hơn = ở trên (ngón duỗi thẳng)
        states[finger] = tip_y < pip_y
    return states


def classify_gesture(img_bgr):
    """
    Classify gesture as 'rock', 'paper', 'scissors', or 'unknown'
    using Mediapipe hand landmarks and simple rule-based logic.
    """
    if img_bgr is None:
        return "unknown"

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(img_rgb)

    if not results.multi_hand_landmarks:
        return "unknown"

    hand_landmarks = results.multi_hand_landmarks[0].landmark
    states = get_finger_states(hand_landmarks)

    extended = [f for f, v in states.items() if v]
    count_ext = len(extended)

    # 0 ngón duỗi -> Rock
    # 4 ngón duỗi -> Paper
    # Chỉ Index + Middle duỗi -> Scissors
    if count_ext == 0:
        return "rock"
    elif count_ext == 4:
        return "paper"
    elif count_ext == 2 and states["index"] and states["middle"] \
            and not states["ring"] and not states["pinky"]:
        return "scissors"
    else:
        return "unknown"


def decide_outcome(player_move, bot_move):
    """
    Decide outcome for PLAYER (win/lose/tie)
    """
    if player_move == bot_move:
        return "tie"

    rules = {
        "rock": "scissors",
        "scissors": "paper",
        "paper": "rock"
    }

    if player_move not in rules or bot_move not in rules:
        return "tie"

    if rules[player_move] == bot_move:
        return "win"
    else:
        return "lose"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
    Nhận ảnh base64 từ client, phân loại cử chỉ, random tay của bot, trả JSON.
    """
    if request.is_json:
        image_data = request.get_json().get("image", "")
    else:
        image_data = request.form.get("image", "")

    if not image_data:
        return jsonify({"error": "no image provided"}), 400

    img = decode_image(image_data)
    player_move = classify_gesture(img)
    bot_move = random.choice(["rock", "paper", "scissors"])
    outcome = decide_outcome(player_move, bot_move)

    return jsonify({
        "your_move": player_move,
        "bot_move": bot_move,
        "outcome": outcome
    })


if __name__ == "__main__":
    # Chỉ cần Flask bình thường, không Socket.IO
    app.run(debug=True)
