# TOOLS.md - Infrastructure & Quick Reference

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## Trading Infrastructure

### MAG7 Signals v10 (Main Bot)
- **Location:** ~/Desktop/stocktrade/mag7-signal-v10/
- **Docker Container:** `mag7-signal-v10`
- **Status Check:** `~/Desktop/stocktrade/mag7-signal-v10/status.sh`
- **Mode:** Paper trading with Alpaca
- **Account ID:** 6ccb8256-4788-4ba9-a53e-6295706ff2ff
- **Auto-Start:** Yes (Docker-managed)

**Key Features:**
- SPY benchmark tracking
- 5% daily loss limit
- Risk management with R/R filtering
- Conservative urgency (0.10)

### Forex Trading Bot
- **Docker Container:** `forex-trading-bot`
- **Status:** Running
- **Auto-Start:** Yes (Docker-managed)

### Kalshi Trading Bot
- **Location:** ~/Desktop/stocktrade/kalshi-trading/
- **Status:** Has critical bugs - NOT safe for live trading
- **Auto-Start:** Never (has unaddressed issues)
- **Corrected Code:** `/Users/tommylu/clawd/kalshi-bot/trading_bot_CORRECTED.py`

**Known Issues:**
- Market making strategy has math errors (guaranteed losses)
- Missing 4 of 5 strategies
- Fixed: Duplicate method bug, risk management now works

## Dashboard

### Larry Status Dashboard
- **Location:** ~/clawd/dashboard/
- **Docker Container:** `larry-dashboard`
- **Status Check:** `~/clawd/dashboard/status.sh`
- **URL:** http://localhost:8888/
- **Auto-Start:** Yes (Docker-managed, `restart: unless-stopped`)

**Purpose:**
- Tracks Larry's activities and status
- Job search progress
- Portfolio projects
- System health monitoring
- Activity logs

**Management Commands:**
```bash
# Check status
~/clawd/dashboard/status.sh

# Restart dashboard
cd ~/clawd/dashboard && docker-compose restart

# View logs
docker logs -f larry-dashboard

# Stop dashboard
cd ~/clawd/dashboard && docker-compose down

# Start dashboard
cd ~/clawd/dashboard && docker-compose up -d
```

**Files Auto-Mounted:** Any changes to files in the dashboard folder are reflected immediately (no rebuild needed).

## Home Automation

### Home Assistant
- **URL:** http://192.168.50.118:8123/
- **Token:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIyY2VmMGU0MDk4ZTI0OWU2YmU0YzlmMjQ5OTA0NDE4NSIsImlhdCI6MTc2OTczMTM2NCwiZXhwIjoyMDg1MDkxMzY0fQ.Yu1Bif1Rjr-TPvlDNY5b140Ol8SEK4MhJ5gy6uF4fjs
- **Entities:**
  - Person tracker
  - Sun sensors
  - Update monitors
  - Backup status
- **HACS:** Installed ✅

### BEDJET Climate Control
- **Entity ID:** `climate.bedjet`
- **🚨 CRITICAL:** Always use "Extended Heat" preset for bed warming
- **Why:** Prevents auto shut-off, designed for all-night use
- **Default Temp:** 88°F when user requests warming
- **Available Presets:**
  - Turbo
  - Extended Heat (use this!)
  - M1: Default
  - M2: sleep winter
  - sleep/wake
  - sleep winter
  - EM

## Media & Entertainment

### Jellyseerr (Media Requests)
- **URL:** http://192.168.50.2:5055
- **API Key:** MTc2NjgwOTM2NjE2NWFhODE0MDVlLWU4MzgtNDAyMi05ZTY4LTZlNTFkYzY3ZjQxZQ==
- **User:** tommy (tommylu3h@gmail.com)
- **Total Requests:** 150
- **Features:**
  - Request movies/shows
  - Approve/decline requests
  - Search content
  - Check request status

## Quick Commands

### Docker Management
```bash
# Check all containers
docker ps -a

# Check for failed containers
docker ps -a | grep -E "Exited|Dead"

# Restart specific bot
docker restart forex-trading-bot

# View logs
docker logs -f forex-trading-bot
```

### Trading Bot Status Checks
```bash
# MAG7 v10 quick status
~/Desktop/stocktrade/mag7-signal-v10/status.sh

# Check git status (for any trading project)
cd ~/Desktop/stocktrade/mag7-signal-v10 && git status
```

### Git Status Checks (All Trading Projects)
```bash
# Check all projects for uncommitted changes
for dir in ~/Desktop/stocktrade/*/; do
  echo "=== $dir ==="
  cd "$dir" && git status --short 2>/dev/null || echo "Not a git repo"
done
```

## Environment Variables

### Trading Bots
- **Alpaca Paper Trading:** Set in `.env` files
- **Kalshi API:** Set in `kalshi_config.secret.json`

### Home Assistant
- Token stored in TOOLS.md for local access only
- **Security:** Never share this token in public contexts

## Skills & Their Uses

| Skill | Purpose | Key Commands |
|-------|---------|--------------|
| apple-notes | Create/view/edit Apple Notes | `memo` CLI |
| apple-reminders | Manage reminders | `remindctl` CLI |
| bird | Twitter/X operations | via cookies |
| github | GitHub interaction | `gh issue`, `gh pr`, `gh run` |
| slack | Slack control | reactions, pinning |
| weather | Weather & forecasts | No API key needed |
| summarize | Transcribe/summarize content | URLs, podcasts, videos |
| coding-agent | Run coding assistants | Codex, Claude Code, OpenCode |

## Monitoring Schedule

### Market Hours (9:30 AM - 4:00 PM ET)
- **Every 2-3 hours:** MAG7 bot status, Dashboard check
- **Morning + Evening:** Docker container health
- **Daily:** Calendar, weather, Home Assistant alerts, Dashboard status update

### After Hours
- Minimal checks (weather only if needed)
- No trading bot checks (markets closed)

## Common Issues & Fixes

### Bot Not Responding
1. Check Docker status: `docker ps -a`
2. Check logs: `docker logs <container>`
3. Restart if needed: `docker restart <container>`

### Weekend Position Spam
- **Issue:** Bot sends "Positions closed for weekend" every cycle
- **Fix:** Already applied - flag ensures message only sends once

### Database Not Saving Signals
- **Issue:** Signals not being logged to database
- **Fix:** Already applied - `insert_signal(signal)` added at line 307

### Kalshi Risk Management Broken
- **Issue:** Duplicate method name `calculate_position_size()` overwrote risk version
- **Fix:** Renamed Kelly version to `calculate_position_size_kelly()`
- **Status:** Fixed ✅

## Notes

- **Privacy:** TOOLS.md contains sensitive info - never load in shared contexts
- **Separation:** Skills are shared, TOOLS.md is unique to this setup
- **Updates:** Add new tools/commands here as discovered
- **Reference:** This is your cheat sheet for quick command lookup

---

*Last Updated: 2026-01-30*
