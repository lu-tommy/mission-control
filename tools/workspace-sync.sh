#!/bin/bash
# workspace-sync.sh - Full workspace sync: commit, hygiene, dashboard update
# Usage: workspace-sync.sh [-p] [-q]
#   -p  Push after commit
#   -q  Quiet mode

set -e

CLAWD_DIR="$HOME/clawd"
TOOLS_DIR="$CLAWD_DIR/tools"
DASHBOARD_DIR="$CLAWD_DIR/dashboard"

PUSH_FLAG=""
QUIET=false

# Parse flags
while getopts "pq" opt; do
    case $opt in
        p) PUSH_FLAG="-p" ;;
        q) QUIET=true ;;
        *) echo "Usage: $0 [-p] [-q]" >&2; exit 1 ;;
    esac
done

log() {
    [ "$QUIET" = false ] && echo "$1"
}

log "━━━ Workspace Sync ━━━"
log ""

# Track what was done
ACTIONS=()

# 1. Run autocommit
log "📦 Checking for uncommitted changes..."
COMMIT_OUTPUT=$("$TOOLS_DIR/autocommit.sh" $PUSH_FLAG 2>&1) || true
if [ -n "$COMMIT_OUTPUT" ]; then
    log "$COMMIT_OUTPUT"
    ACTIONS+=("committed changes")
else
    log "   (no changes to commit)"
fi
log ""

# 2. Run memory hygiene
log "🧹 Running memory hygiene..."
if [ -x "$TOOLS_DIR/memory-hygiene.sh" ]; then
    HYGIENE_OUTPUT=$("$TOOLS_DIR/memory-hygiene.sh" 2>&1) || true
    if echo "$HYGIENE_OUTPUT" | grep -q "✓\|fixed\|cleaned"; then
        log "$HYGIENE_OUTPUT"
        ACTIONS+=("cleaned memory")
    else
        log "   (memory is clean)"
    fi
else
    log "   ⚠ memory-hygiene.sh not found"
fi
log ""

# 3. Update dashboard sync timestamp
log "📊 Updating dashboard..."
SYNC_FILE="$DASHBOARD_DIR/last-sync.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TIMESTAMP_HUMAN=$(date "+%Y-%m-%d %H:%M:%S")

# Get git status for dashboard
cd "$CLAWD_DIR"
LAST_COMMIT=$(git log -1 --format="%h - %s" 2>/dev/null || echo "unknown")
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

cat > "$SYNC_FILE" << EOF
{
  "lastSync": "$TIMESTAMP",
  "lastSyncHuman": "$TIMESTAMP_HUMAN",
  "lastCommit": "$LAST_COMMIT",
  "branch": "$BRANCH",
  "actionsPerformed": $(printf '%s\n' "${ACTIONS[@]}" | jq -R . | jq -s .)
}
EOF
log "   ✓ Updated last-sync.json"
ACTIONS+=("updated dashboard")
log ""

# 4. Summary
log "━━━ Summary ━━━"
if [ ${#ACTIONS[@]} -eq 0 ]; then
    log "Nothing to do - workspace is clean!"
else
    for action in "${ACTIONS[@]}"; do
        log "  ✓ $action"
    done
fi
log ""
log "Sync completed at $TIMESTAMP_HUMAN"
