const socket = io();
const videoPlayer = document.getElementById('main-video');
const historyList = document.getElementById('gesture-history-list');
const connectionStatus = document.getElementById('connection-status');
const camStatus = document.getElementById('cam-status');
const toastContainer = document.getElementById('toast-container');

// State
let lastActionTime = 0;

// Socket Events
socket.on('connect', () => {
  console.log('Connected to Backend');
  connectionStatus.classList.add('active');
  camStatus.classList.add('active'); // Assumption since we connected
});

socket.on('disconnect', () => {
  console.log('Disconnected from Backend');
  connectionStatus.classList.remove('active');
  camStatus.classList.remove('active');
});

socket.on('gesture_detected', (data) => {
  handleGesture(data.action);
});

// Gesture Handling
function handleGesture(action) {
  // Cooldown on client side mostly for UI spam prevention, logic is effectively backend driven
  const now = Date.now();

  // Add to history
  addHistory(action);
  showToast(action);

  // Apply Logic
  switch (action) {
    case "Play":
      videoPlayer.play();
      break;
    case "Pause":
      videoPlayer.pause();
      break;
    case "VolUp":
      if (videoPlayer.volume < 0.9) videoPlayer.volume += 0.1;
      else videoPlayer.volume = 1.0;
      break;
    case "VolDown":
      if (videoPlayer.volume > 0.1) videoPlayer.volume -= 0.1;
      else videoPlayer.volume = 0.0;
      break;
    case "Forward":
      videoPlayer.currentTime += 10;
      break;
    case "Rewind":
      videoPlayer.currentTime -= 10;
      break;
  }
}

function addHistory(action) {
  const li = document.createElement('div');
  li.className = 'history-item';

  const time = new Date().toLocaleTimeString();
  li.innerHTML = `<span>${action}</span> <span style="color:var(--text-secondary); font-size: 0.8em;">${time}</span>`;

  historyList.prepend(li); // Add to top
  if (historyList.children.length > 20) {
    historyList.removeChild(historyList.lastChild);
  }
}

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';

  // Icon mapping
  let icon = 'Info';
  if (message === 'Play') icon = '▶';
  if (message === 'Pause') icon = '⏸';
  if (message === 'VolUp') icon = '🔊';
  if (message === 'VolDown') icon = '🔉';
  if (message === 'Forward') icon = '⏩';
  if (message === 'Rewind') icon = '⏪';

  toast.innerHTML = `<span style="font-size:1.2em">${icon}</span> <span>${message} Detected</span>`;

  toastContainer.appendChild(toast);

  // Automatic removal handled by CSS animation, but DOM removal needed
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// File Upload
document.getElementById('video-upload').addEventListener('change', async function (e) {
  const file = e.target.files[0];
  if (!file) return;

  // Create FormData
  const formData = new FormData();
  formData.append('video', file);

  try {
    // Show loading state (simple)
    document.querySelector('.upload-btn').textContent = "Uploading...";

    const response = await fetch('/upload_video', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (result.status === 'success') {
      videoPlayer.src = result.url;
      videoPlayer.play(); // Auto play on load
      document.querySelector('.upload-btn').textContent = "Upload Video";
    } else {
      alert('Upload failed: ' + result.message);
    }
  } catch (err) {
    console.error(err);
    alert('Upload failed');
  }
});
