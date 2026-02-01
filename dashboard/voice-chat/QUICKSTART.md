# 🦞 Larry Voice Chat - Quick Start

**Status:** 🟡 Frontend complete - API integration in progress

## What's Built ✅

- Voice chat interface at `http://localhost:8888/voice-chat/`
- Push-to-Talk mode (hold button to speak)
- Continuous listening mode (toggle mic on/off)
- Real-time transcription
- Text-to-Speech (hear Larry's responses)
- Settings panel (voice speed, language, etc.)
- Mobile-friendly design
- API server (Node.js, port 8889)

## What's Working Now

**You can:**
- Open `http://localhost:8888/voice-chat/` in Chrome/Edge
- See the voice chat interface
- Push the microphone button
- See transcription (placeholder responses)
- Adjust settings

**What needs work:**
- **API Integration** - Messages go to placeholder, not Larry yet
- When you speak, it shows: "I heard you say: X. This is a placeholder..."

## Next Steps

### 1. Test the Interface
```bash
# Open in browser (Chrome or Edge)
open http://localhost:8888/voice-chat/
```

### 2. Start the API Server (Optional for now)
```bash
cd ~/clawd/dashboard/voice-chat
npm install
npm start
```
The API server runs on port 8889 but isn't fully connected to Larry yet.

### 3. Real Integration (Needs Work)
The `api-server.js` needs to connect to Clawdbot's sessions API:
- Currently sends to `/tools/invoke` with sessions_send
- But sessions_send doesn't return the response text
- Need to either use sessions_history polling or find a better approach

## Files

| File | Description |
|------|-------------|
| `index.html` | Voice chat UI |
| `voice-chat.js` | STT/TTS logic (Web Speech API) |
| `style.css` | Styling and animations |
| `api-server.js` | Node.js proxy server |
| `package.json` | NPM dependencies |
| `README.md` | Full documentation |

## Dashboard Integration

This project is tracked in your dashboard at `http://localhost:8888/`:
- Look under **In Progress** → "Voice Chat Interface"
- Subtasks show what's done vs what's left
- Activity feed updates automatically

## Browser Support

| Browser | STT (Speech-to-Text) | TTS (Text-to-Speech) |
|---------|---------------------|----------------------|
| Chrome | ✅ Full support | ✅ Full support |
| Edge | ✅ Full support | ✅ Full support |
| Safari | ⚠️ Partial | ✅ Full support |
| Firefox | ❌ Limited | ✅ Full support |

**Recommendation:** Use Chrome or Edge on desktop.

## How It Works (Architecture)

```
You speak 🎤
    ↓
Web Speech API (STT)
    ↓
Text → voice-chat.js
    ↓
/api/chat (Node.js server)
    ↓
Clawdbot sessions API ⚠️ (needs integration)
    ↓
Larry's response
    ↓
Web Speech API (TTS)
    ↓
You hear it 🔊
```

## Current Blocking Issue

**Problem:** `sessions_send` tool sends a message but doesn't return the response text.

**Options to fix:**
1. Poll `sessions_history` after sending (latency issue)
2. Use Clawdbot's WebSocket connection (if exposed)
3. Find Clawdbot's REST API for getting session responses
4. Build a custom message router with webhooks

**Status:** Researching best approach. Frontend is ready and waiting.

---

*Built by Larry for Tommy 🦞*
