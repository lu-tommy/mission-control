#!/bin/bash
# autocommit.sh - Auto-commit changes in ~/clawd with smart messages
# Usage: autocommit.sh [-p] [-q]
#   -p  Push after commit
#   -q  Quiet mode (less output)

set -e

CLAWD_DIR="$HOME/clawd"
PUSH=false
QUIET=false

# Parse flags
while getopts "pq" opt; do
    case $opt in
        p) PUSH=true ;;
        q) QUIET=true ;;
        *) echo "Usage: $0 [-p] [-q]" >&2; exit 1 ;;
    esac
done

cd "$CLAWD_DIR"

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    # No changes - exit silently
    exit 0
fi

# Get changed files for smart commit message
CHANGED_FILES=$(git status --porcelain)
ADDED=$(echo "$CHANGED_FILES" | grep -c "^A\|^??" || true)
MODIFIED=$(echo "$CHANGED_FILES" | grep -c "^M\|^ M" || true)
DELETED=$(echo "$CHANGED_FILES" | grep -c "^D\|^ D" || true)

# Identify what areas changed
AREAS=()
if echo "$CHANGED_FILES" | grep -q "memory/"; then
    AREAS+=("memory")
fi
if echo "$CHANGED_FILES" | grep -q "tools/"; then
    AREAS+=("tools")
fi
if echo "$CHANGED_FILES" | grep -q "dashboard/"; then
    AREAS+=("dashboard")
fi
if echo "$CHANGED_FILES" | grep -q "MEMORY.md\|SOUL.md\|AGENTS.md\|TOOLS.md"; then
    AREAS+=("core")
fi
if echo "$CHANGED_FILES" | grep -q "skills/"; then
    AREAS+=("skills")
fi
if echo "$CHANGED_FILES" | grep -q "taskboard/"; then
    AREAS+=("tasks")
fi
if echo "$CHANGED_FILES" | grep -q "twitter/"; then
    AREAS+=("twitter")
fi

# Build commit message
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
if [ ${#AREAS[@]} -eq 0 ]; then
    AREA_STR="misc"
else
    AREA_STR=$(IFS=","; echo "${AREAS[*]}")
fi

# Build stats string
STATS=""
[ "$ADDED" -gt 0 ] && STATS+="+$ADDED "
[ "$MODIFIED" -gt 0 ] && STATS+="~$MODIFIED "
[ "$DELETED" -gt 0 ] && STATS+="-$DELETED"
STATS=$(echo "$STATS" | xargs)  # trim whitespace

COMMIT_MSG="[$AREA_STR] Auto-sync ($STATS) - $TIMESTAMP"

# Stage all changes
git add -A

# Commit
git commit -m "$COMMIT_MSG" --quiet

if [ "$QUIET" = false ]; then
    echo "✓ Committed: $COMMIT_MSG"
fi

# Push if requested
if [ "$PUSH" = true ]; then
    if git push --quiet 2>/dev/null; then
        [ "$QUIET" = false ] && echo "✓ Pushed to remote"
    else
        echo "⚠ Push failed (check remote/auth)" >&2
    fi
fi

exit 0
