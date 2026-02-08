def recognize_gesture(lm):
    up = lambda t, m: lm[t].y < lm[m].y

    thumb = lm[4].x < lm[5].x
    index = up(8, 5)
    middle = up(12, 9)
    ring = up(16, 13)
    pinky = up(20, 17)

    fingers = [thumb, index, middle, ring, pinky]
    count = fingers.count(True)

    if count == 0:
        return "CLOSED_FIST"

    if count == 5:
        gap = abs(lm[4].x - lm[8].x)
        return "THUMB_GAP" if gap > 0.08 else "FIVE_JOINED"

    if index and middle and ring and not thumb and not pinky:
        return "THREE_FINGERS"

    if index and not middle and not ring and not pinky:
        return "INDEX"

    if pinky and not index and not middle and not ring:
        return "PINKY_FORWARD" if lm[20].x > lm[17].x else "PINKY_BACKWARD"

    return None
