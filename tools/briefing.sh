#!/bin/bash
#
# Morning Briefing Generator
# Generates a daily summary with weather, calendar, work progress, job search, tasks, and bot status
#
# Usage: ./briefing.sh [--quiet]
#   --quiet: Only output markdown (no terminal formatting)
#

set -euo pipefail

# Config
DASHBOARD_DIR="$HOME/clawd/dashboard"
JOB_SEARCH_DIR="$HOME/clawd/job-search"
STATUS_FILE="$DASHBOARD_DIR/larry-status.json"
JOB_FILE="$JOB_SEARCH_DIR/job-search-results.md"
LOCATION="${BRIEFING_LOCATION:-New York}"

# Colors (disabled if --quiet)
QUIET=false
if [[ "${1:-}" == "--quiet" ]]; then
    QUIET=true
fi

# Date/time helpers
NOW=$(date +%s)
TWELVE_HOURS_AGO=$((NOW - 43200))
TODAY=$(date +%Y-%m-%d)
TODAY_DISPLAY=$(date "+%A, %B %d, %Y")
TIME_NOW=$(date "+%I:%M %p")

# Output accumulator
OUTPUT=""

add() {
    OUTPUT+="$1"$'\n'
}

# ============================================
# Header
# ============================================
add "# ☀️ Morning Briefing"
add "**${TODAY_DISPLAY}** | ${TIME_NOW}"
add ""

# ============================================
# 1. Weather
# ============================================
add "## 🌤️ Weather"
add ""

# Fetch weather from wttr.in (compact format, URL encode the location)
LOCATION_ENCODED=$(echo "$LOCATION" | sed 's/ /%20/g')
WEATHER=$(curl -s --max-time 5 "wttr.in/${LOCATION_ENCODED}?format=%l:+%c+%t" 2>/dev/null || echo "")
WEATHER_DETAIL=$(curl -s --max-time 5 "wttr.in/${LOCATION_ENCODED}?format=%C,+humidity+%h,+wind+%w" 2>/dev/null || echo "")

if [[ -n "$WEATHER" && "$WEATHER" != *"Unknown"* ]]; then
    add "**$WEATHER**"
    if [[ -n "$WEATHER_DETAIL" ]]; then
        add "*$WEATHER_DETAIL*"
    fi
else
    add "⚠️ Weather data unavailable"
fi
add ""

# ============================================
# 2. Calendar Events Today
# ============================================
add "## 📅 Today's Calendar"
add ""

# Try to get calendar events using icalBuddy (if installed) or AppleScript
if command -v icalBuddy &> /dev/null; then
    EVENTS=$(icalBuddy -nc -nrd -npn -ea -b "• " eventsToday 2>/dev/null || echo "")
    if [[ -n "$EVENTS" && "$EVENTS" != *"No events"* ]]; then
        add "$EVENTS"
    else
        add "No events scheduled for today ✨"
    fi
else
    # Fallback: Try AppleScript
    EVENTS=$(osascript -e '
        set today to current date
        set tomorrow to today + (1 * days)
        set eventList to ""
        tell application "Calendar"
            repeat with cal in calendars
                set evs to (every event of cal whose start date ≥ today and start date < tomorrow)
                repeat with e in evs
                    set eventList to eventList & "• " & (summary of e) & " at " & time string of (start date of e) & linefeed
                end repeat
            end repeat
        end tell
        return eventList
    ' 2>/dev/null || echo "")
    
    if [[ -n "$EVENTS" ]]; then
        add "$EVENTS"
    else
        add "No events scheduled for today ✨"
    fi
fi
add ""

# ============================================
# 3. Overnight Work Summary (Last 12 hours)
# ============================================
add "## 🌙 Overnight Activity"
add ""

if [[ -f "$STATUS_FILE" ]]; then
    # Parse activity from last 12 hours using jq
    if command -v jq &> /dev/null; then
        ACTIVITY_COUNT=$(jq '[.activity[] | select(.timestamp != null)] | length' "$STATUS_FILE" 2>/dev/null || echo "0")
        COMPLETED_COUNT=$(jq '.tasks.done | length' "$STATUS_FILE" 2>/dev/null || echo "0")
        
        # Get recent activity (top 5)
        RECENT_ACTIVITY=$(jq -r '.activity[:5][] | "• \(.action)"' "$STATUS_FILE" 2>/dev/null || echo "")
        
        if [[ -n "$RECENT_ACTIVITY" ]]; then
            add "**Recent Activity ($ACTIVITY_COUNT entries):**"
            add "$RECENT_ACTIVITY"
            add ""
            add "**Tasks Completed:** $COMPLETED_COUNT"
        else
            add "No overnight activity logged"
        fi
        
        # Current status
        CURRENT_STATUS=$(jq -r '.larryStatus // "unknown"' "$STATUS_FILE" 2>/dev/null)
        CURRENT_FOCUS=$(jq -r '.currentFocus // "None"' "$STATUS_FILE" 2>/dev/null)
        add ""
        add "**Current Status:** $CURRENT_STATUS"
        add "**Focus:** $CURRENT_FOCUS"
    else
        add "⚠️ jq not installed - cannot parse activity log"
    fi
else
    add "Dashboard status file not found"
fi
add ""

# ============================================
# 4. Job Search Status
# ============================================
add "## 💼 Job Search Status"
add ""

if [[ -f "$JOB_FILE" ]]; then
    # Count jobs found (lines starting with ###)
    JOB_COUNT=$(grep -c "^### " "$JOB_FILE" 2>/dev/null || echo "0")
    TOP_PICKS=$(grep -c "PERFECT FIT\|EXCELLENT FIT\|GREAT FIT" "$JOB_FILE" 2>/dev/null || echo "0")
    
    add "**Roles Found:** $JOB_COUNT"
    add "**Top Picks:** $TOP_PICKS"
    
    # Extract top pick titles
    if [[ "$TOP_PICKS" -gt 0 ]]; then
        add ""
        add "**Best Matches:**"
        MATCHES=$(grep -B1 "PERFECT FIT\|EXCELLENT FIT" "$JOB_FILE" 2>/dev/null | grep "^### " | head -3 | sed 's/^### [0-9]*\. /• /' | sed 's/ ⭐.*//' || echo "")
        if [[ -n "$MATCHES" ]]; then
            add "$MATCHES"
        fi
    fi
    
    # Check for application tracking if exists
    if [[ -f "$JOB_SEARCH_DIR/applications.json" ]]; then
        APPLIED=$(jq '.applications | length' "$JOB_SEARCH_DIR/applications.json" 2>/dev/null || echo "0")
        RESPONSES=$(jq '[.applications[] | select(.status == "response" or .status == "interview")] | length' "$JOB_SEARCH_DIR/applications.json" 2>/dev/null || echo "0")
        add ""
        add "**Applications Submitted:** $APPLIED"
        add "**Responses/Interviews:** $RESPONSES"
    fi
else
    add "No job search results file found"
fi
add ""

# ============================================
# 5. Tasks Due Today
# ============================================
add "## ✅ Tasks Due Today"
add ""

if [[ -f "$STATUS_FILE" ]] && command -v jq &> /dev/null; then
    # Get tasks due today
    TASKS_TODAY=$(jq -r --arg today "$TODAY" '
        [.tasks.backlog[], .tasks.inProgress[]? // empty] | 
        map(select(.dueDate != null and (.dueDate | startswith($today)))) |
        .[] | "• **\(.title)** (\(.priority) priority)"
    ' "$STATUS_FILE" 2>/dev/null || echo "")
    
    if [[ -n "$TASKS_TODAY" ]]; then
        add "$TASKS_TODAY"
    else
        add "No tasks due today 🎉"
    fi
    
    # Also show goals progress
    DAILY_TARGET=$(jq -r '.goals.daily.target // 0' "$STATUS_FILE" 2>/dev/null)
    DAILY_COMPLETED=$(jq -r '.goals.daily.completed // 0' "$STATUS_FILE" 2>/dev/null)
    STREAK=$(jq -r '.streak // 0' "$STATUS_FILE" 2>/dev/null)
    
    add ""
    add "**Daily Goal Progress:** $DAILY_COMPLETED / $DAILY_TARGET"
    add "**Current Streak:** $STREAK days 🔥"
else
    add "Cannot read tasks from dashboard"
fi
add ""

# ============================================
# 6. Trading Bot Status
# ============================================
add "## 🤖 Trading Bots"
add ""

# Check Docker container status
if command -v docker &> /dev/null; then
    # Get trading bot containers
    MAG7_STATUS=$(docker ps -a --filter "name=mag7" --format "{{.Status}}" 2>/dev/null | head -1 || echo "Not found")
    FOREX_STATUS=$(docker ps -a --filter "name=forex" --format "{{.Status}}" 2>/dev/null | head -1 || echo "Not found")
    DASHBOARD_STATUS=$(docker ps -a --filter "name=larry-dashboard" --format "{{.Status}}" 2>/dev/null | head -1 || echo "Not found")
    
    # Format status with emoji
    format_status() {
        local status="$1"
        if [[ "$status" == *"Up"* ]]; then
            echo "✅ Running ($status)"
        elif [[ "$status" == *"Exited"* ]]; then
            echo "⚠️ Stopped ($status)"
        elif [[ "$status" == "Not found" ]]; then
            echo "❓ Not found"
        else
            echo "❓ $status"
        fi
    }
    
    add "| Bot | Status |"
    add "|-----|--------|"
    add "| MAG7 Signal v10 | $(format_status "$MAG7_STATUS") |"
    add "| Forex Bot | $(format_status "$FOREX_STATUS") |"
    add "| Larry Dashboard | $(format_status "$DASHBOARD_STATUS") |"
    
    # Check for any alerts (containers that exited unexpectedly)
    FAILED=$(docker ps -a --filter "status=exited" --filter "status=dead" --format "{{.Names}}: {{.Status}}" 2>/dev/null | grep -E "mag7|forex|trading" || echo "")
    if [[ -n "$FAILED" ]]; then
        add ""
        add "**⚠️ Alerts:**"
        echo "$FAILED" | while read -r line; do
            add "• $line"
        done
    fi
else
    add "Docker not available - cannot check bot status"
fi
add ""

# ============================================
# Footer
# ============================================
add "---"
add "*Generated by briefing.sh at $(date "+%Y-%m-%d %H:%M:%S")*"

# ============================================
# Output
# ============================================
echo "$OUTPUT"
