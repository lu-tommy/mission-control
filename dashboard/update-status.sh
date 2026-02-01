#!/bin/bash
# Helper script to update Larry's status dashboard
# Usage: ./update-status.sh <action> [args...]
#
# Actions:
#   status <working|idle|sleeping>  - Set Larry's status
#   focus "text"                    - Set current focus
#   activity "text" <category>      - Add activity entry
#   complete <task-id>              - Mark task as complete
#   start <task-id>                 - Move task to in-progress

JSON_FILE="/Users/tommylu/clawd/dashboard/larry-status.json"

case "$1" in
  status)
    # Update Larry's status
    jq --arg status "$2" '.larryStatus = $status | .lastUpdated = (now | strftime("%Y-%m-%dT%H:%M:%S-05:00"))' "$JSON_FILE" > tmp.$$.json && mv tmp.$$.json "$JSON_FILE"
    echo "Status updated to: $2"
    ;;
  focus)
    # Update current focus
    jq --arg focus "$2" '.currentFocus = $focus | .lastUpdated = (now | strftime("%Y-%m-%dT%H:%M:%S-05:00"))' "$JSON_FILE" > tmp.$$.json && mv tmp.$$.json "$JSON_FILE"
    echo "Focus updated to: $2"
    ;;
  activity)
    # Add activity entry
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S-05:00")
    jq --arg action "$2" --arg category "${3:-system}" --arg ts "$TIMESTAMP" \
      '.activity = [{"timestamp": $ts, "action": $action, "category": $category}] + .activity | .lastUpdated = $ts' "$JSON_FILE" > tmp.$$.json && mv tmp.$$.json "$JSON_FILE"
    echo "Activity added: $2"
    ;;
  *)
    echo "Usage: $0 <status|focus|activity> [args...]"
    echo ""
    echo "Examples:"
    echo "  $0 status working"
    echo "  $0 focus 'Building job search automation'"
    echo "  $0 activity 'Found 5 new job listings' jobs"
    ;;
esac
