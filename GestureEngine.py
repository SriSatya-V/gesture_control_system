import cv2
import time
import math
import HandTrackingModule as htm
import screen_brightness_control as sbc
import pyautogui
from collections import deque

# Disable pyautogui failsafe for non-mouse actions
pyautogui.FAILSAFE = False

class GestureEngine:
    def __init__(self):
        # Webcam Capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
             self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        # Support 2 hands (Left or Right interchangeably)
        self.detector = htm.HandDetector(detectionCon=0.75, maxHands=2)
        
        # State
        self.gesture_cooldown = 0
        self.last_gesture = None
        self.volume_last_time = 0
        self.brightness_last_time = 0
        
        # Swipe Logic (Track Wrist X landmark of the leading hand)
        self.wrist_x_history = deque(maxlen=10) 
        self.swipe_threshold = 50 
        
        # Cooldown for discrete gestures (Play/Pause/Swipe)
        self.discrete_cooldown = 1.0 

        # Initial Brightness
        try:
            self.current_brightness = sbc.get_brightness()[0]
        except:
            self.current_brightness = 50

    def get_frame_data(self):
        success, img = self.cap.read()
        if not success:
            return None, None

        img = cv2.flip(img, 1) # Mirror for natural interaction
        img = self.detector.findHands(img, draw=True)
        
        current_gesture = None
        
        if self.detector.results.multi_hand_landmarks:
            # 1. Update Swipe History (using the first hand detected)
            h, w, c = img.shape
            handLms = self.detector.results.multi_hand_landmarks[0]
            wrist_x = int(handLms.landmark[0].x * w)
            self.wrist_x_history.append((time.time(), wrist_x))

            # Loop through all detected hands to find a gesture
            for idx, handLms in enumerate(self.detector.results.multi_hand_landmarks):
                # Retrieve handedness (Left/Right)
                handedness = self.detector.results.multi_handedness[idx].classification[0].label
                
                # Get landmarks and bbox
                lmList, bbox = self.detector.findPosition(img, handNo=idx, draw=False)
                
                if lmList:
                    # Execute Strict Priority Hierarchy Logic
                    res_gesture, res_color = self.detect_gesture(img, lmList, handedness)
                    
                    if res_gesture:
                        current_gesture = res_gesture
                        msg = current_gesture
                        if "Brightness" in msg:
                            msg = f"Brightness: {int(self.current_brightness)}%"
                        
                        # Draw feedback near the hand
                        cv2.putText(img, f"{msg}", (lmList[0][1], lmList[0][2] - 50), 
                                    cv2.FONT_HERSHEY_DUPLEX, 0.8, res_color, 2)
                        
                        # Stop checking other hands if a gesture is detected
                        break

        ret, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        
        return frame_bytes, current_gesture

    def detect_gesture(self, img, lmList, handedness):
        now = time.time()
        
        # Map finger states (1=extended, 0=curled)
        # Custom logic for thumb handedness
        fingers = []
        # Thumb
        if handedness == "Right":
            fingers.append(1 if lmList[4][1] > lmList[3][1] else 0)
        else: # Left Hand
            fingers.append(1 if lmList[4][1] < lmList[3][1] else 0)
        # 4 Fingers
        for id in [8, 12, 16, 20]:
            fingers.append(1 if lmList[id][2] < lmList[id-2][2] else 0)

        # --- 1. DYNAMIC SWIPES (Highest Priority) ---
        if len(self.wrist_x_history) >= 5:
            start_time, start_x = self.wrist_x_history[0]
            end_time, end_x = self.wrist_x_history[-1]
            if (now - start_time) < 0.4:
                displacement = end_x - start_x
                if abs(displacement) > self.swipe_threshold:
                    if now - self.gesture_cooldown > self.discrete_cooldown:
                        self.gesture_cooldown = now
                        if displacement > 0:
                            pyautogui.press('right')
                            return "Forward", (0, 255, 255)
                        else:
                            pyautogui.press('left')
                            return "Rewind", (255, 100, 100)
                    else:
                        return None, (0,0,0) # Locked in cooldown

        # --- 2. BRIGHTNESS CONTROL (Pinch) ---
        # Middle, Ring, Pinky must be closed
        if fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            x1, y1 = lmList[4][1], lmList[4][2] # Thumb Tip
            x2, y2 = lmList[8][1], lmList[8][2] # Index Tip
            dist = math.hypot(x2 - x1, y2 - y1)
            
            if now - self.brightness_last_time > 0.15:
                self.brightness_last_time = now
                if dist < 40: # User said 30, 40 is more stable
                    self.current_brightness = max(0, self.current_brightness - 5)
                    sbc.set_brightness(int(self.current_brightness))
                    return "Brightness Down", (0, 165, 255)
                elif dist > 110: # User said 100, 110 is safer
                    self.current_brightness = min(100, self.current_brightness + 5)
                    sbc.set_brightness(int(self.current_brightness))
                    return "Brightness Up", (0, 255, 255)
            # Register generic brightness mode if fingers held this way
            return "Brightness", (255, 215, 0)

        # --- 3. VOLUME CONTROL (Thumb Direction) ---
        # Index, Middle, Ring, Pinky must be closed (Fist with thumb out)
        if fingers[1:] == [0, 0, 0, 0]:
            thumb_tip_y = lmList[4][2]
            thumb_mcp_y = lmList[2][2]
            
            if now - self.volume_last_time > 0.2:
                self.volume_last_time = now
                if thumb_tip_y < thumb_mcp_y - 25: # Smaller Y = Higher on screen
                    pyautogui.press('volumeup')
                    return "VolUp", (0, 255, 0)
                elif thumb_tip_y > thumb_mcp_y + 25: # Larger Y = Lower on screen
                    pyautogui.press('volumedown')
                    return "VolDown", (255, 0, 0)

        # --- 4. PLAY/PAUSE (Fallback) ---
        if now - self.gesture_cooldown > self.discrete_cooldown:
            # Play: All 5 fingers extended
            if fingers == [1, 1, 1, 1, 1]:
                self.gesture_cooldown = now
                return "Play", (0, 255, 0)
            # Pause: All 5 fingers folded
            if fingers == [0, 0, 0, 0, 0]:
                self.gesture_cooldown = now
                return "Pause", (0, 0, 255)

        return None, (0,0,0)

    def release(self):
        self.cap.release()
