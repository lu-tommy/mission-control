# Morning Briefing Setup

## Quick Start

```bash
# Run manually
~/clawd/tools/briefing.sh

# Output to file
~/clawd/tools/briefing.sh > ~/briefing.md

# Quiet mode (no terminal colors)
~/clawd/tools/briefing.sh --quiet
```

## Cron Job Setup (7am Daily)

### Option 1: User Crontab (Recommended)

```bash
# Edit your crontab
crontab -e

# Add this line for 7am daily:
0 7 * * * /Users/tommylu/clawd/tools/briefing.sh > /Users/tommylu/clawd/morning-briefing.md 2>&1

# To also send via Telegram (if you have a bot setup):
0 7 * * * /Users/tommylu/clawd/tools/briefing.sh | /usr/local/bin/telegram-send --stdin
```

### Option 2: launchd (macOS Native)

Create `~/Library/LaunchAgents/com.clawd.briefing.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clawd.briefing</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/tommylu/clawd/tools/briefing.sh</string>
    </array>
    <key>StandardOutPath</key>
    <string>/Users/tommylu/clawd/morning-briefing.md</string>
    <key>StandardErrorPath</key>
    <string>/Users/tommylu/clawd/logs/briefing-error.log</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>BRIEFING_LOCATION</key>
        <string>New York</string>
    </dict>
</dict>
</plist>
```

Then load it:

```bash
# Create logs directory
mkdir -p ~/clawd/logs

# Load the job
launchctl load ~/Library/LaunchAgents/com.clawd.briefing.plist

# Check if loaded
launchctl list | grep briefing

# Unload if needed
launchctl unload ~/Library/LaunchAgents/com.clawd.briefing.plist
```

## Configuration

Set custom location via environment variable:

```bash
BRIEFING_LOCATION="Brooklyn" ~/clawd/tools/briefing.sh
```

## Dependencies

- **Required:** `jq` (for JSON parsing) - install with `brew install jq`
- **Optional:** `icalBuddy` (for calendar) - install with `brew install ical-buddy`
- **Optional:** Docker (for trading bot status)

## Telegram Integration

To send via Telegram, you can use Clawdbot's message tool or a Telegram bot:

```bash
# Via Clawdbot (if available)
~/clawd/tools/briefing.sh | clawdbot message send --channel telegram --message -

# Or save and send via heartbeat
~/clawd/tools/briefing.sh > ~/clawd/morning-briefing.md
# Then Larry can read and forward it
```

## Troubleshooting

```bash
# Test weather API
curl "wttr.in/New%20York?format=3"

# Test calendar access
icalBuddy eventsToday

# Test docker access
docker ps

# Check cron is running
grep CRON /var/log/system.log
```
