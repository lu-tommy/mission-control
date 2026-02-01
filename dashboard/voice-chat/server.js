#!/usr/bin/env node

/**
 * Larry Voice Chat API Server
 * Connects to real Clawdbot API for AI responses
 */

const http = require('http');
const url = require('url');

const PORT = 8889;
const CLAWDBOT_URL = 'http://127.0.0.1:18789';
const CLAWDBOT_TOKEN = 'b423058d3faec9d936e51e8d35c902e0c082301946be5579';

function corsHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function sendJSON(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

// Call Clawdbot API
async function callClawdbot(tool, args) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({ tool, args });
    
    const options = {
      hostname: '127.0.0.1',
      port: 18789,
      path: '/tools/invoke',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CLAWDBOT_TOKEN}`,
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Parse error: ' + e.message));
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(60000, () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
    
    req.write(payload);
    req.end();
  });
}

// Get AI response using sessions_spawn
async function getAIResponse(message) {
  log(`Getting AI response for: "${message.substring(0, 50)}..."`);

  try {
    // Spawn a GLM subagent for the response
    const spawnResult = await callClawdbot('sessions_spawn', {
      task: message,
      model: 'zai/glm-4.7',
      timeoutSeconds: 30,
      cleanup: 'delete',
      label: 'voice-chat',
      thinking: 'low'  // Fast responses for voice
    });

    const childKey = spawnResult.result?.details?.childSessionKey;
    if (!childKey) {
      log('No child session key returned');
      return "I heard you, but I'm having trouble responding right now. Try again?";
    }

    log(`Spawned child session: ${childKey}`);

    // Poll for response (up to 25 seconds)
    for (let i = 0; i < 17; i++) {
      await sleep(1500);
      
      const histResult = await callClawdbot('sessions_history', {
        sessionKey: childKey,
        limit: 5,
        includeTools: false
      });

      const messages = histResult.result?.details?.messages || [];
      
      for (const msg of messages) {
        if (msg.role === 'assistant') {
          let text = extractText(msg.content);
          
          // Clean up response
          text = text.trim();
          if (text && text.length > 5 && !text.includes('NO_REPLY') && !text.includes('HEARTBEAT_OK')) {
            log(`Got response: "${text.substring(0, 60)}..."`);
            return text;
          }
        }
      }
      
      log(`Polling ${i + 1}/17...`);
    }

    return "I'm taking too long to think. Try asking again?";

  } catch (e) {
    log(`Error: ${e.message}`);
    return "Something went wrong on my end. Try again?";
  }
}

function extractText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(b => b.type === 'text')
      .map(b => b.text)
      .join('\n');
  }
  return '';
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const server = http.createServer(async (req, res) => {
  corsHeaders(res);

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname;

  // Health check
  if (pathname === '/api/health') {
    sendJSON(res, 200, { status: 'ok', model: 'zai/glm-4.7', uptime: process.uptime() });
    return;
  }

  // Chat endpoint
  if (pathname === '/api/chat' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => { body += chunk; });
    
    req.on('end', async () => {
      try {
        const { message } = JSON.parse(body);
        
        if (!message || typeof message !== 'string' || !message.trim()) {
          sendJSON(res, 400, { error: 'Message required' });
          return;
        }

        log(`Message: "${message.trim().substring(0, 50)}..."`);
        
        const response = await getAIResponse(message.trim());

        sendJSON(res, 200, { response, model: 'zai/glm-4.7' });

      } catch (e) {
        log(`Error: ${e.message}`);
        sendJSON(res, 500, { error: 'Server error' });
      }
    });
    
    return;
  }

  sendJSON(res, 404, { error: 'Not found' });
});

// Graceful shutdown
process.on('SIGINT', () => { log('Shutting down...'); server.close(() => process.exit(0)); });
process.on('SIGTERM', () => { log('Terminating...'); server.close(() => process.exit(0)); });

server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') {
    log(`Port ${PORT} in use. Retrying in 2s...`);
    setTimeout(() => server.listen(PORT), 2000);
  } else {
    log(`Server error: ${e.message}`);
    process.exit(1);
  }
});

server.listen(PORT, () => {
  log(`Voice API running on http://localhost:${PORT}`);
  log('Using model: zai/glm-4.7 (via Clawdbot API)');
});
