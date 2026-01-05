from flask import Flask, render_template, Response, request, send_from_directory
from flask_socketio import SocketIO, emit
import os
import GestureEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")

# Global Gesture Engine
engine = list() 
# Using a list to hold the instance so we can lazily init or handle restarts if needed, 
# although global var is also fine.
gesture_engine = GestureEngine.GestureEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return {'status': 'error', 'message': 'No file part'}, 400
    file = request.files['video']
    if file.filename == '':
        return {'status': 'error', 'message': 'No selected file'}, 400
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return {'status': 'success', 'filename': filename, 'url': f"/static/uploads/{filename}"}

def generate_frames():
    while True:
        frame_bytes, gesture = gesture_engine.get_frame_data()
        
        if gesture:
            # Emit socket event
            # We need to use the app context or socketio's broadcase capability
            socketio.emit('gesture_detected', {'action': gesture})
            print(f"Emitted: {gesture}")

        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            break

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # host='0.0.0.0' allows external access (like from a real smart TV on the network)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
