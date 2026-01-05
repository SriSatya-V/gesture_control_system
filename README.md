# Gesture Controlled Interface

This project uses OpenCV and MediaPipe to control system volume and brightness using hand gestures.

## Prerequisites

- Python 3.7+
- Webcam

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the controller script:
   ```bash
   python Controller.py
   ```

2. **Controls**:
   - **Volume**: Use your Index Finger and Thumb. Pinch them closer or further apart to change volume.
   - **Brightness**: Use your Pinky Finger and Thumb (ensure Index finger is not pinched). Pinch closer/further to change brightness.
   - Press `q` to exit.

## Files

- `Controller.py`: Main application loop.
- `HandTrackingModule.py`: Helper class for hand detection.
- `requirements.txt`: Python package dependencies.
