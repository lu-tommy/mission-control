# Larry Voice Chat

Voice-enabled chat interface for Larry the Lobster 🦞

## Features

- **Push-to-Talk** mode: Hold the microphone button to speak
- **Continuous** mode: Toggle mic on/off for ongoing conversation
- **Real-time transcription**: See what you're saying as you speak
- **Text-to-Speech**: Hear Larry's responses spoken back to you
- **Settings panel**: Customize voice, language, and behavior
- **Chat history**: Saves conversations automatically
- **Mobile-friendly**: Works on phones and tablets

## Setup

### 1. Start the Dashboard

If the dashboard isn't already running:

```bash
cd ~/clawd/dashboard
docker-compose up -d
```

Check status:
```bash
~/clawd/dashboard/status.sh
```

### 2. Access Voice Chat

Open your browser and go to:
```
http://localhost:8888/voice-chat/
```

## Usage

### Push-to-Talk Mode (Default)

1. Click and hold the **Hold to Talk** button
2. Speak your message
3. Release the button to send
4. Larry will respond and speak back

### Continuous Mode

1. Tap the **Continuous** mode button (🔊)
2. Tap the microphone icon to start/stop listening
3. Speak normally - transcription appears in real-time
4. Tap **Send** to send your message to Larry

### Settings

Click the **⚙️** settings icon to customize:
- **STT Engine**: Web Speech API (free) or Whisper API
- **Audio Output**: Choose speaker/headphones
- **Speech Rate**: 0.5x to 2.0x speed
- **Language**: English (US/UK)
- **Auto-play**: Automatically hear Larry's responses
- **Save History**: Keep chat history between sessions

## Technical Details

### Browser Compatibility

- **Chrome/Edge**: Full support (Web Speech API)
- **Safari**: TTS works, STT may require HTTPS
- **Firefox**: Limited STT support
- **Mobile**: Works on iOS Safari (iOS 14.1+) and Chrome Android

### Architecture

```
Browser (voice-chat/)
    ↓ Web Speech API
    ↓ (transcribed text)
Backend API (needs setup)
    ↓ forwards to
Larry (Clawdbot)
    ↓ response text
Backend API
    ↓
Browser (TTS plays audio)
```

### Current Status

✅ **Working:**
- Web Speech API for speech-to-text
- Web Speech API for text-to-speech
- Push-to-talk and continuous modes
- Settings panel
- Chat history UI
- API proxy server (runs on port 8889)

⚠️ **Needs Setup:**
- **Clawdbot API integration** - voice-chat.js needs to call the actual Clawdbot API
- API server connects but returns placeholders
- Need to configure proper message routing

## Running the Voice Chat Server

The voice chat includes a Node.js API server:

```bash
cd ~/clawd/dashboard/voice-chat
npm install
npm start
```

The server runs on **port 8889**:
- HTTP API: `http://localhost:8889/api/chat`
- WebSocket: `ws://localhost:8889`

## Connecting to Larry's API

The API server (`api-server.js`) is a placeholder that needs to be connected to Clawdbot's messaging system.

**Current implementation:** Returns placeholder responses
**Needs:** Integration with Clawdbot's `sessions_send` or REST API

To implement:
1. Find Clawdbot's API endpoint for sending messages to the main session
2. Update `forwardToLarry()` function in `api-server.js`
3. Update `CONFIG.chatEndpoint` in `voice-chat.js` to point to the API server

**Example:**
```javascript
// In api-server.js
async function forwardToLarry(message) {
  // Call Clawdbot's sessions_send or REST API
  const response = await fetch('http://localhost:3000/api/session/agent:main:main/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  return response.data.reply;
}
```

## Troubleshooting

### "Speech recognition not supported"
- Use Chrome or Edge browser
- Check if microphone permission is granted
- On Safari, you may need HTTPS

### No audio output
- Check volume settings
- Try a different voice in settings
- Some browsers require user interaction before playing audio

### Placeholder responses
- The backend API needs to be set up
- Currently in demo mode

## Files

- `index.html` - Main interface
- `voice-chat.js` - Core functionality (STT, TTS, chat)
- `style.css` - Styling and animations
- `README.md` - This file

## Next Steps

1. ✅ Interface built and styled
2. ⏳ Connect backend API to Clawdbot
3. ⏳ Test end-to-end voice conversation
4. ⏳ Deploy for mobile access

---

*Built for Tommy's voice chat with Larry 🦞*
