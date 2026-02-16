import cv2
import time
from hand_detector import HandDetector
from gesture_recognizer import recognize_gesture
from controller import perform_action
from config import SCROLL_THRESHOLD, VOLUME_DELAY


# Initialize Camera and Detector
cap = cv2.VideoCapture(0)
detector = HandDetector()

#  Variables for Logic 
prev_gesture = None
prev_y = 0  # To track previous vertical position for scrolling
scroll_threshold = SCROLL_THRESHOLD # Sensitivity for air scroll (higher = need more movement)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip frame for natural interaction (mirror mode)
    frame = cv2.flip(frame, 1)
    
    # Detect Hand
    result = detector.process_frame(frame)

    if result.multi_hand_landmarks:
        # Get the first hand detected
        hand = result.multi_hand_landmarks[0]
        detector.draw_landmarks(frame, hand)

        # Recognize Gesture
        gesture = recognize_gesture(hand.landmark)

        if gesture:
            #  SPECIAL HANDLING: BRIGHTNESS AIR SCROLL - This is a continuous action based on movement, not just a one-shot command.
            if gesture == "BRIGHTNESS_SCROLL":
                # Use the Middle Finger MCP (Knuckle) - Landmark 9 - for stable tracking
                current_y = hand.landmark[9].y

                # Check if we have a previous point to compare against
                if prev_y != 0:
                    # Note: In OpenCV, Y decreases as you go UP, increases as you go DOWN.
                    
                    # Moved Up
                    if current_y < prev_y - scroll_threshold:
                        perform_action("BRIGHTNESS_UP")
                        prev_y = current_y # Update immediately for smooth scrolling
                    
                    # Moved Down
                    elif current_y > prev_y + scroll_threshold:
                        perform_action("BRIGHTNESS_DOWN")
                        prev_y = current_y # Update immediately

                # If first time entering scroll mode, just set the reference point
                else:
                    prev_y = current_y

            #  HANDLING OTHER GESTURES 
            else:
                # Reset brightness tracking when gesture changes
                prev_y = 0

                # LOGIC: 
                # 1. Volume commands should repeat (Continuous)
                # 2. Other commands (Play/Pause, Next) should fire only once per gesture change (One-shot)
                
                is_volume = gesture in ["VOLUME_UP", "VOLUME_DOWN"]
                is_new_gesture = gesture != prev_gesture

                if is_volume or is_new_gesture:
                    perform_action(gesture)
                    # Small delay for volume to prevent it from rocketing 0-100 instantly
                    if is_volume:
                        time.sleep(VOLUME_DELAY) 

            # Update previous gesture memory
            prev_gesture = gesture

            # Display Gesture Name on Screen
            cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (0, 255, 0), 2, cv2.LINE_AA)

        else:
            # Hand detected but no specific gesture recognized
            prev_gesture = None
            prev_y = 0

    cv2.imshow("Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
"""
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
"""