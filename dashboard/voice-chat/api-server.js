#!/usr/bin/env node

/**
 * Larry Voice Chat API
 * Uses sessions_spawn - waits for subagent to complete
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = 8889;

const CLAWDBOT = {
  baseUrl: 'http://127.0.0.1:18789',
  token: 'b423058d3faec9d936e51e8d35c902e0c082301946be5579'
};

// CORS - allow requests from dashboard
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

app.use(express.json());
app.use(express.static(__dirname));

const clients = new Set();

app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'Message required' });

    console.log('Voice:', message);
    const startTime = Date.now();

    // Spawn subagent and wait for completion
    const response = await fetch(`${CLAWDBOT.baseUrl}/tools/invoke`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CLAWDBOT.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool: 'sessions_spawn',
        args: {
          task: `Voice message from Tommy. Be conversational, warm, brief (2-3 sentences max). Reply with TEXT ONLY - do not use TTS or any tools. He said: "${message}"`,
          label: 'voice-response',
          timeoutSeconds: 30,
          runTimeoutSeconds: 25,
          cleanup: 'delete'
        }
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    // The spawn returns immediately with childSessionKey
    // But the ACTUAL response comes via a callback/announcement
    // For now, poll the child session for the response
    
    const childKey = data.result?.details?.childSessionKey;
    if (!childKey) {
      console.log('No child session, raw:', JSON.stringify(data).substring(0, 300));
      return res.json({ response: "Give me a sec..." });
    }

    console.log('Child session:', childKey);

    // Poll for response (subagent typically takes 4-10 seconds)
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 1500));

      const histRes = await fetch(`${CLAWDBOT.baseUrl}/tools/invoke`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CLAWDBOT.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tool: 'sessions_history',
          args: { sessionKey: childKey, limit: 5 }
        })
      });

      const histData = await histRes.json();
      const messages = histData.result?.details?.messages || [];

      for (const msg of messages) {
        if (msg.role === 'assistant') {
          let text = '';
          if (typeof msg.content === 'string') {
            text = msg.content;
          } else if (Array.isArray(msg.content)) {
            text = msg.content.filter(b => b.type === 'text').map(b => b.text).join('\n');
          }
          
          text = text.trim();
          if (text && text.length > 10 && !text.includes('NO_REPLY')) {
            console.log(`Response (${elapsed}s):`, text.substring(0, 80));
            return res.json({ response: text });
          }
        }
      }
      console.log(`Polling ${i+1}/15...`);
    }

    res.json({ response: "Still thinking... try again?" });

  } catch (error) {
    console.error('Error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// WebSocket support
wss.on('connection', (ws) => {
  console.log('WS connected');
  clients.add(ws);

  ws.on('message', async (data) => {
    try {
      const parsed = JSON.parse(data);
      if (parsed.type === 'message') {
        ws.send(JSON.stringify({ type: 'status', text: 'Thinking...' }));
        
        const resp = await fetch(`http://localhost:${PORT}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: parsed.text })
        });
        const result = await resp.json();
        ws.send(JSON.stringify({ type: 'response', text: result.response || result.error }));
      }
    } catch (error) {
      ws.send(JSON.stringify({ type: 'error', text: error.message }));
    }
  });

  ws.on('close', () => clients.delete(ws));
});

app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

server.listen(PORT, () => console.log(`Voice API ready: http://localhost:${PORT}`));
