"""
Air Drawing with Hand Gestures
Control a virtual drawing canvas using your webcam and MediaPipe.

Gestures:
  - Index finger only: draw
  - Index + middle fingers: move the pointer without drawing
  - Closed fist: erase
  - Open palm (four fingers raised): clear the canvas

Keyboard:
  1-5: change brush color
  + / -: change brush size
  S: save the canvas
  C: clear the canvas
  Q or ESC: quit
"""

import os
import time

import cv2
import mediapipe as mp
import numpy as np


# BGR colors used by OpenCV
COLORS = {
    "1": ("Blue", (255, 0, 0)),
    "2": ("Green", (0, 200, 0)),
    "3": ("Red", (0, 0, 255)),
    "4": ("Yellow", (0, 220, 255)),
    "5": ("White", (255, 255, 255)),
}


def finger_is_up(landmarks, tip_id: int, pip_id: int) -> bool:
    """Return True when a finger tip is above its middle joint."""
    return landmarks[tip_id].y < landmarks[pip_id].y


def detect_gesture(hand_landmarks) -> str:
    """Classify a small set of useful gestures from hand landmarks."""
    lm = hand_landmarks.landmark

    index_up = finger_is_up(lm, 8, 6)
    middle_up = finger_is_up(lm, 12, 10)
    ring_up = finger_is_up(lm, 16, 14)
    pinky_up = finger_is_up(lm, 20, 18)

    # Ignore the thumb because its orientation changes with hand rotation.
    raised = [index_up, middle_up, ring_up, pinky_up]

    if all(raised):
        return "CLEAR"
    if not any(raised):
        return "ERASE"
    if index_up and middle_up and not ring_up and not pinky_up:
        return "MOVE"
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "DRAW"
    return "PAUSE"


def draw_hud(frame, gesture: str, color_name: str, brush_size: int) -> None:
    """Draw simple instructions and current settings on the camera frame."""
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 105), (25, 25, 25), -1)
    cv2.putText(
        frame, f"MODE: {gesture}", (15, 32),
        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2,
    )
    cv2.putText(
        frame, f"Color: {color_name} | Brush: {brush_size}px",
        (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1,
    )
    cv2.putText(
        frame, "1-5 Colors  +/- Brush  S Save  C Clear  Q Quit",
        (15, 91), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1,
    )


def main() -> None:
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError(
            "Could not open the webcam. Check camera permissions or try another camera index."
        )

    # Request a practical webcam resolution; the camera may choose a nearby size.
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    canvas = None
    previous_point = None
    current_color_name = "Blue"
    current_color = COLORS["1"][1]
    brush_size = 8
    eraser_size = 45
    previous_gesture = "PAUSE"
    last_clear_time = 0.0

    print("Air Drawing started. Press Q or ESC to quit.")

    try:
        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65,
        ) as hands:
            while True:
                success, frame = camera.read()
                if not success:
                    print("Could not read a frame from the webcam.")
                    break

                # Mirror the image so movement feels natural.
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]

                if canvas is None:
                    canvas = np.zeros((height, width, 3), dtype=np.uint8)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame.flags.writeable = False
                results = hands.process(rgb_frame)
                rgb_frame.flags.writeable = True

                gesture = "NO HAND"
                cursor = None

                if results.multi_hand_landmarks:
                    hand = results.multi_hand_landmarks[0]
                    mp_draw.draw_landmarks(
                        frame, hand, mp_hands.HAND_CONNECTIONS
                    )

                    gesture = detect_gesture(hand)
                    index_tip = hand.landmark[8]
                    cursor = (
                        min(int(index_tip.x * width), width - 1),
                        min(int(index_tip.y * height), height - 1),
                    )

                    if gesture == "CLEAR":
                        # Clear once when the open-palm gesture is first detected.
                        now = time.time()
                        if previous_gesture != "CLEAR" and now - last_clear_time > 1.0:
                            canvas[:] = 0
                            previous_point = None
                            last_clear_time = now
                    elif gesture == "DRAW" and cursor is not None:
                        if previous_point is not None:
                            cv2.line(
                                canvas, previous_point, cursor,
                                current_color, brush_size, cv2.LINE_AA,
                            )
                        previous_point = cursor
                    elif gesture == "ERASE" and cursor is not None:
                        if previous_point is not None:
                            cv2.line(
                                canvas, previous_point, cursor,
                                (0, 0, 0), eraser_size, cv2.LINE_AA,
                            )
                        previous_point = cursor
                    else:
                        # MOVE and PAUSE never leave a mark.
                        previous_point = None

                    if cursor is not None:
                        marker_color = (0, 255, 255) if gesture == "MOVE" else current_color
                        cv2.circle(frame, cursor, 9, marker_color, cv2.FILLED)
                else:
                    previous_point = None

                previous_gesture = gesture

                # Combine the black canvas with the live camera image.
                canvas_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
                _, drawing_mask = cv2.threshold(
                    canvas_gray, 10, 255, cv2.THRESH_BINARY
                )
                drawing_mask_inv = cv2.bitwise_not(drawing_mask)
                camera_background = cv2.bitwise_and(
                    frame, frame, mask=drawing_mask_inv
                )
                drawing_foreground = cv2.bitwise_and(
                    canvas, canvas, mask=drawing_mask
                )
                output = cv2.add(camera_background, drawing_foreground)

                draw_hud(output, gesture, current_color_name, brush_size)
                cv2.imshow("Air Drawing - Hand Gesture Control", output)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                elif chr(key) in COLORS:
                    current_color_name, current_color = COLORS[chr(key)]
                elif key in (ord("+"), ord("=")):
                    brush_size = min(brush_size + 2, 40)
                elif key in (ord("-"), ord("_")):
                    brush_size = max(brush_size - 2, 2)
                elif key == ord("c"):
                    canvas[:] = 0
                    previous_point = None
                elif key == ord("s"):
                    os.makedirs("output", exist_ok=True)
                    filename = time.strftime("output/air_drawing_%Y%m%d_%H%M%S.png")
                    if cv2.imwrite(filename, canvas):
                        print(f"Drawing saved to: {filename}")
                    else:
                        print("Could not save the drawing.")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Air Drawing closed.")


if __name__ == "__main__":
    main()
