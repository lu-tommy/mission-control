// Larry Voice Chat - Fixed Version
const API_URL = 'http://localhost:8889/api/chat';

let recognition = null;
let isListening = false;
let mode = 'push'; // 'push' or 'continuous'

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  console.log('Voice chat initializing...');
  
  // Check for speech recognition support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    setStatus('Speech not supported', 'error');
    return;
  }

  // Setup recognition
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onstart = () => {
    isListening = true;
    document.getElementById('listeningIndicator').style.display = 'flex';
    document.getElementById('pttButton').classList.add('active');
  };

  recognition.onend = () => {
    isListening = false;
    document.getElementById('listeningIndicator').style.display = 'none';
    document.getElementById('pttButton').classList.remove('active');
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    // Show transcription preview and update text
    const preview = document.getElementById('transcriptionPreview');
    const textEl = document.getElementById('transcriptionText');
    textEl.textContent = transcript;
    preview.style.display = 'flex';
    
    // If final result in push mode, send immediately
    if (event.results[event.results.length - 1].isFinal && mode === 'push') {
      sendMessage(transcript);
      preview.style.display = 'none';
      textEl.textContent = '';
    }
  };

  recognition.onerror = (event) => {
    console.error('Speech error:', event.error);
    setStatus('Error: ' + event.error, 'error');
    isListening = false;
    document.getElementById('listeningIndicator').style.display = 'none';
  };

  // Push-to-talk button
  const pttBtn = document.getElementById('pttButton');
  pttBtn.addEventListener('mousedown', startListening);
  pttBtn.addEventListener('mouseup', stopListening);
  pttBtn.addEventListener('mouseleave', stopListening);
  pttBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startListening(); });
  pttBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopListening(); });

  // Continuous mode toggle button
  const micToggle = document.getElementById('micToggleBtn');
  micToggle.addEventListener('click', toggleContinuous);

  // Mode buttons
  document.getElementById('pushModeBtn').addEventListener('click', () => setMode('push'));
  document.getElementById('continuousModeBtn').addEventListener('click', () => setMode('continuous'));

  // Settings button
  document.getElementById('settingsBtn').addEventListener('click', () => {
    document.getElementById('settingsModal').classList.add('active');
  });
  document.getElementById('closeSettingsBtn').addEventListener('click', () => {
    document.getElementById('settingsModal').classList.remove('active');
  });
  document.getElementById('settingsModal').addEventListener('click', (e) => {
    if (e.target.id === 'settingsModal') {
      document.getElementById('settingsModal').classList.remove('active');
    }
  });

  // Speech rate slider
  const rateSlider = document.getElementById('speechRate');
  rateSlider.addEventListener('input', () => {
    document.getElementById('speechRateValue').textContent = rateSlider.value + 'x';
  });

  // Send button (for continuous mode - review before sending)
  document.getElementById('sendBtn').addEventListener('click', () => {
    const textEl = document.getElementById('transcriptionText');
    const text = textEl.textContent.trim();
    if (text) {
      sendMessage(text);
      textEl.textContent = '';
      document.getElementById('transcriptionPreview').style.display = 'none';
    }
  });

  // Clear button
  document.getElementById('clearBtn').addEventListener('click', () => {
    document.getElementById('transcriptionText').textContent = '';
    document.getElementById('transcriptionPreview').style.display = 'none';
  });

  // Test API connection
  testConnection();
});

function testConnection() {
  setStatus('Connecting...', 'connecting');
  fetch('http://localhost:8889/api/health')
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        setStatus('Connected', 'connected');
      } else {
        setStatus('API error', 'error');
      }
    })
    .catch(err => {
      console.error('Connection failed:', err);
      setStatus('Offline', 'error');
    });
}

function setStatus(text, type) {
  const statusBadge = document.getElementById('connectionStatus');
  const statusText = document.getElementById('connectionText');
  statusText.textContent = text;
  statusBadge.className = 'status-badge ' + type;
}

function setMode(newMode) {
  mode = newMode;
  document.getElementById('pushModeBtn').classList.toggle('active', mode === 'push');
  document.getElementById('continuousModeBtn').classList.toggle('active', mode === 'continuous');
  document.getElementById('pttSection').style.display = mode === 'push' ? 'block' : 'none';
  document.getElementById('continuousControls').style.display = mode === 'continuous' ? 'flex' : 'none';
  
  // Stop listening and reset state when switching modes
  if (isListening) {
    recognition.stop();
  }
  
  // Reset recognition mode
  if (recognition) {
    recognition.continuous = (mode === 'continuous');
  }
  
  // Reset mic icon for continuous mode
  document.getElementById('micIcon').textContent = '🎤';
  
  // Hide transcription preview when switching modes
  document.getElementById('transcriptionPreview').style.display = 'none';
  document.getElementById('transcriptionText').textContent = '';
}

function startListening() {
  if (!recognition || isListening) return;
  try {
    recognition.start();
  } catch (e) {
    console.error('Start error:', e);
  }
}

function stopListening() {
  if (!recognition || !isListening) return;
  recognition.stop();
}

function toggleContinuous() {
  if (isListening) {
    recognition.stop();
    document.getElementById('micIcon').textContent = '🎤';
  } else {
    recognition.continuous = true;
    recognition.start();
    document.getElementById('micIcon').textContent = '⏹️';
  }
}

async function sendMessage(text) {
  if (!text.trim()) return;
  
  addMessage('user', text);
  setStatus('Sending...', 'connecting');
  document.getElementById('processingIndicator').style.display = 'flex';

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    const data = await response.json();
    document.getElementById('processingIndicator').style.display = 'none';
    setStatus('Connected', 'connected');

    if (data.response) {
      addMessage('larry', data.response);
      speak(data.response);
    } else if (data.error) {
      addMessage('system', 'Error: ' + data.error);
    }
  } catch (err) {
    console.error('Send error:', err);
    document.getElementById('processingIndicator').style.display = 'none';
    setStatus('Error', 'error');
    addMessage('system', 'Failed to reach Larry: ' + err.message);
  }
}

function addMessage(sender, text) {
  const container = document.getElementById('chatMessages');
  const msg = document.createElement('div');
  msg.className = 'message ' + sender;
  
  const avatar = sender === 'larry' ? '🦞' : (sender === 'user' ? '👤' : '⚠️');
  msg.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <div class="message-text">${escapeHtml(text)}</div>
      <div class="message-time">${new Date().toLocaleTimeString()}</div>
    </div>
  `;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  
  const autoPlay = document.getElementById('autoPlay')?.checked ?? true;
  if (!autoPlay) return;

  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = parseFloat(document.getElementById('speechRate')?.value || 1);
  utterance.lang = 'en-US';
  speechSynthesis.speak(utterance);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
