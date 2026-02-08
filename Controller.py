import pyautogui
import screen_brightness_control as sbc
from config import BRIGHTNESS_STEP

def perform_action(gesture):

    # Play (open palm)
    if gesture == "OPEN_FIST":
        pyautogui.press("playpause")

    # Pause (closed fist)
    elif gesture == "CLOSED_FIST":
        pyautogui.press("playpause")

    # Volume Up (Index + Middle + Ring)
    elif gesture == "THREE_FINGERS":
        pyautogui.press("volumeup")

    # Volume Down (Index only)
    elif gesture == "INDEX":
        pyautogui.press("volumedown")

    # Forward
    elif gesture == "PINKY_FORWARD":
        pyautogui.press("right")

    # Backward
    elif gesture == "PINKY_BACKWARD":
        pyautogui.press("left")

    # Brightness Down (5 fingers joined)
    elif gesture == "FIVE_JOINED":
        current = sbc.get_brightness()[0]
        sbc.set_brightness(max(current - BRIGHTNESS_STEP, 0))

    # Brightness Up (Thumb gap with 4 fingers)
    elif gesture == "THUMB_GAP":
        current = sbc.get_brightness()[0]
        sbc.set_brightness(min(current + BRIGHTNESS_STEP, 100))
