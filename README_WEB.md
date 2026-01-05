# Smart Gesture Control Web Interface

This module adds a modern Web UI to the Gesture Control System.

## Features
- **Dark Mode Dashboard**: Smart TV inspired aesthetics.
- **Webcam Integration**: Real-time gesture detection stream.
- **Video Player**: Upload and play videos (MP4, AVI, MKV) with gesture control.
- **Gestures Supported**:
  - 🖐 **Open Hand**: Play
  - ✊ **Closed Fist**: Pause
  - 👍 / 👎 **Thumbs**: Volume Up/Down
  - 👈 / 👉 **Swipe**: Rewind / Fast Forward

## Setup & Run

The project relies on the existing virtual environment.

1. **Activate Virtual Environment**:
   ```powershell
   .\.venv\Scripts\activate
   ```

2. **Install Web Dependencies** (if not already installed):
   ```powershell
   pip install flask flask-socketio
   ```
   *(Note: `mediapipe` and `opencv-python` should already be installed)*

3. **Run the Application**:
   ```powershell
   python app.py
   ```

4. **Access the Dashboard**:
   Open your browser (Chrome/Edge recommended) and navigate to:
   [http://localhost:5000](http://localhost:5000)

## Architecture
- **app.py**: Flask server handling video uploads and webcam streaming. Uses `GestureEngine` to process frames.
- **GestureEngine.py**: Wrapper around `HandTrackingModule` to perform detection without opening a local CV2 window.
- **static/js/script.js**: Handles WebSockets, updates UI, and controls the HTML5 Video Element.
- **static/css/style.css**: Styling for the dashboard.
