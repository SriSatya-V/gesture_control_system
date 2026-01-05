import cv2
import time
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ffpyplayer.player import MediaPlayer

class GestureVideoController:
    def __init__(self, video_path='Video.mp4'):
        self.video_path = video_path
        
        # Video Capture (OpenCV)
        self.cap_video = cv2.VideoCapture(video_path)
        
        # Audio Player (ffpyplayer)
        # ff_opts={'paused':True} to start paused if needed, but we start playing
        self.player = MediaPlayer(video_path)
        
        # Video Properties
        self.fps = self.cap_video.get(cv2.CAP_PROP_FPS)
        if self.fps == 0: self.fps = 30
        self.total_frames = int(self.cap_video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps

        # Webcam Capture
        self.cap_webcam = cv2.VideoCapture(0)
        if not self.cap_webcam.isOpened():
             # Fallback
             self.cap_webcam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
             
        if not self.cap_webcam.isOpened():
            print("CRITICAL: Webcam could not be opened.")
        
        # Hand Detector
        self.detector = htm.HandDetector(detectionCon=0.7, maxHands=1)
        
        # Volume Control Setup
        self.setup_volume_control()
        
        # State Variables
        self.is_paused = False
        self.gesture_cooldown = 0
        self.prev_x = 0
        self.swipe_threshold = 20
        self.history_x = []
        
        print("Gesture Video Controller Started with Audio")

    def setup_volume_control(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.EndpointVolume
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            self.vol_range = self.volume.GetVolumeRange() 
            self.min_vol = self.vol_range[0]
            self.max_vol = self.vol_range[1]
        except Exception as e:
            print(f"Volume setup failed: {e}")
            self.volume = None

    def change_volume(self, increase=True):
        if not self.volume: return
        current_vol = self.volume.GetMasterVolumeLevel()
        step = 2.0
        if increase:
            new_vol = min(current_vol + step, self.max_vol)
        else:
            new_vol = max(current_vol - step, self.min_vol)
        self.volume.SetMasterVolumeLevel(new_vol, None)

    def seek_video(self, forward=True):
        # Current Method: using timestamp for syncing
        current_pts = self.player.get_pts()
        if current_pts is None: current_pts = 0
        
        skip = 10.0 # seconds
        if forward:
            target = current_pts + skip
        else:
            target = max(0, current_pts - skip)
            
        # Seek Audio Player
        self.player.seek(target, relative=False)
        # Seek OpenCV Video
        # We might not need accurate seek here if we sync frames to audio, 
        # but let's do it to be safe
        self.cap_video.set(cv2.CAP_PROP_POS_FRAMES, int(target * self.fps))

    def detect_gesture(self, img, lmList):
        # Fingers Up Logic
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
            # Simple heuristic: Tip above wrist = Up (y is inverted)
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
                    return "Forward", (0, 255, 255)
                else: # Left
                    return "Rewind", (255, 100, 100)
                    
        self.prev_x = curr_x
        return None, (0,0,0)

    def run(self):
        cv2.namedWindow("Smart Gesture Player", cv2.WINDOW_NORMAL)
        
        while True:
            # Sync Logic
            # Read frame from OpenCV
            # Read audio frame from ffpyplayer to keep sync
            
            audio_frame, val = self.player.get_frame()
            
            if self.is_paused:
                 # Pause logic: we just don't advance
                 # ffpyplayer handles pause via set_pause
                 # But we need to make sure we don't block
                 pass
            else:
                # If val == 'eof': break
                success_vid, img_video = self.cap_video.read()
                if not success_vid:
                    # Loop
                    self.cap_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.player.seek(0, relative=False)
                    success_vid, img_video = self.cap_video.read()

            # Webcam
            success_cam, img_cam = self.cap_webcam.read()
            if success_cam:
                img_cam = cv2.flip(img_cam, 1)
                img_cam = self.detector.findHands(img_cam)
                lmList, bbox = self.detector.findPosition(img_cam, draw=True)
                
                if len(lmList) != 0:
                     if time.time() - self.gesture_cooldown > 0.5:
                        gesture, color = self.detect_gesture(img_cam, lmList)
                        if gesture:
                            self.gesture_cooldown = time.time()
                            if gesture == "Play":
                                self.is_paused = False
                                self.player.set_pause(False)
                            elif gesture == "Pause":
                                self.is_paused = True
                                self.player.set_pause(True)
                            elif gesture == "VolUp":
                                self.change_volume(True)
                            elif gesture == "VolDown":
                                self.change_volume(False)
                            elif gesture == "Forward":
                                self.seek_video(True)
                            elif gesture == "Rewind":
                                self.seek_video(False)

                # PIP
                if success_vid:
                    h_vid, w_vid = img_video.shape[:2]
                    h_small, w_small = int(h_vid * 0.25), int(w_vid * 0.25)
                    img_cam_small = cv2.resize(img_cam, (w_small, h_small))
                    img_video[0:h_small, w_vid-w_small:w_vid] = img_cam_small
                    cv2.imshow("Smart Gesture Player", img_video)
            
            # Use 'val' from audio for sync wait
            if val != 'eof' and audio_frame is not None:
                # Audio frame available
                img, t = audio_frame
                # We could display 'img' if it were a video player only driven by ffpyplayer
                # But we use OpenCV for 'img_video'.
                pass
            
            # WaitKey: use a small delay. Real sync is harder but 30ms is approx 30fps
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
                
        self.cap_video.release()
        self.cap_webcam.release()
        self.player = None # Close player
        cv2.destroyAllWindows()

if __name__ == '__main__':
    app = GestureVideoController()
    app.run()
