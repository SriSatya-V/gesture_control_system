import cv2
from hand_detector import HandDetector
from gesture_recognizer import recognize_gesture
from controller import perform_action

cap = cv2.VideoCapture(0)
detector = HandDetector()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    result = detector.process_frame(frame)

    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        detector.draw_landmarks(frame, hand)

        gesture = recognize_gesture(hand.landmark)
        if gesture:
            perform_action(gesture)

    cv2.imshow("Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
