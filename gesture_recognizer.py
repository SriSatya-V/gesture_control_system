def recognize_gesture(lm):
    # Helper: Check if finger tip is higher (y is smaller) than the joint
    # Using PIP joints (6, 10, 14, 18) is more accurate than MCP (5, 9, 13, 17) for open/closed detection
    up = lambda t, m: lm[t].y < lm[m].y

    # Determine finger states
    # Thumb: Assumes Right Hand facing camera (or mirrored Left). 
    # Logic: Tip (4) is to the left of IP joint (5)
    thumb = lm[4].x < lm[5].x
    
    # Fingers: Tip vs PIP joint
    index = up(8, 6)
    middle = up(12, 10)
    ring = up(16, 14)
    pinky = up(20, 18)

    fingers = [thumb, index, middle, ring, pinky]
    count = fingers.count(True)

    # 1. CLOSE (Closed Fist) 
    if count == 0:
        return "CLOSE"

    # 2. PLAY_PAUSE (All 5 fingers Open) 
    if count == 5:
        return "PLAY_PAUSE"

    # 3. NEXT VIDEO (Thumb + Index + Middle + Ring)
    # Pinky is DOWN
    if thumb and index and middle and ring and not pinky:
        return "NEXT_VIDEO"

    # 4. BRIGHTNESS (Four Fingers: Index + Middle + Ring + Pinky) 
    # Thumb is DOWN. This triggers the scroll mode.
    # Logic in main.py must decide if it's "UP" or "DOWN" based on movement.
    if index and middle and thumb and not pinky and not ring:
        return "BRIGHTNESS_SCROLL"

    # 5. VOLUME UP (Index + Middle + Ring) 
    # Thumb and Pinky are DOWN
    if index and middle and ring and not thumb and not pinky:
        return "VOLUME_UP"

    # 6. PREVIOUS VIDEO (Thumb + Index / L-Shape) 
    # Middle, Ring, Pinky are DOWN
    if thumb and index and not middle and not ring and not pinky:
        return "PREVIOUS_VIDEO"

    # 7. FORWARD (Index + Pinky / Rock Symbol) 
    # Middle and Ring are DOWN
    if index and pinky and not middle and not ring:
        return "FORWARD"

    #  8. VOLUME DOWN (Index only) 
    # Thumb, Middle, Ring, Pinky are DOWN
    if index and not middle and not ring and not pinky and not thumb:
        return "VOLUME_DOWN"

    # 9. BACKWARD (Thumb only)
    # All fingers DOWN
    if thumb and not index and not middle and not ring and not pinky:
        return "BACKWARD"

    return None
