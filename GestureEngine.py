import cv2
import time
import HandTrackingModule as htm

class GestureEngine:
    def __init__(self):
        # Webcam Capture
        self.cap = cv2.VideoCapture(0)
        # Fallback if 0 doesn't work
        if not self.cap.isOpened():
             self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        self.detector = htm.HandDetector(detectionCon=0.7, maxHands=1)
        
        # State
        self.gesture_cooldown = 0
        self.prev_x = 0
        self.swipe_threshold = 20
        self.history_x = []
        self.last_gesture = None
        self.last_gesture_time = 0

    def get_frame_data(self):
        success, img = self.cap.read()
        if not success:
            return None, None

        img = cv2.flip(img, 1)
        img = self.detector.findHands(img)
        lmList, bbox = self.detector.findPosition(img, draw=True)
        
        current_gesture = None

        if len(lmList) != 0:
            # Only process gestures if cooldown has passed
            if time.time() - self.gesture_cooldown > 0.5:
                current_gesture, color = self.detect_gesture(img, lmList)
                if current_gesture:
                    self.gesture_cooldown = time.time()
                    self.last_gesture = current_gesture
                    self.last_gesture_time = time.time()
                    
                    # Visual feedback on the frame (optional, since we have UI overlays)
                    cv2.putText(img, f"GESTURE: {current_gesture}", (10, 50), 
                                cv2.FONT_HERSHEY_PLAIN, 2, color, 3)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        
        return frame_bytes, current_gesture

    def detect_gesture(self, img, lmList):
        fingers = self.detector.fingersUp() # [Thumb, Index, Middle, Ring, Pinky]
        total_fingers = fingers.count(1)
        
        # 1. Fist Open (Play) - All fingers up
        if total_fingers == 5:
            return "Play", (0, 255, 0)
            
        # 2. Fist Closed (Pause)
        if fingers[1:] == [0, 0, 0, 0]:
             if fingers[0] == 0:
                 return "Pause", (0, 0, 255)
        
        # 3. Thumbs Up/Down (Volume)
        if fingers[1:] == [0, 0, 0, 0]:
            thumb_tip_y = lmList[4][2]
            wrist_y = lmList[0][2]
            if thumb_tip_y < wrist_y:
                 return "VolUp", (255, 255, 0)
            elif thumb_tip_y > wrist_y:
                 return "VolDown", (255, 0, 255)

        # 4. Swipes (Rewind/Forward) using Index Finger x-movement
        curr_x = lmList[8][1] # Index tip
        
        self.history_x.append(curr_x)
        if len(self.history_x) > 5: self.history_x.pop(0)
        
        if len(self.history_x) >= 2:
            dx = curr_x - self.prev_x
            self.prev_x = curr_x
            
            if abs(dx) > self.swipe_threshold:
                if dx > 0: # Right
                    return "Forward", (0, 255, 255) # Assuming flip was handled, right is right
                else: # Left
                    return "Rewind", (255, 100, 100)
                    
        self.prev_x = curr_x
        return None, (0,0,0)

    def release(self):
        self.cap.release()
