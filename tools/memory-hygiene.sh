#!/bin/bash
# memory-hygiene.sh - Prevent memory bloat and fragmentation
# Run manually or via cron/heartbeat

set -e
MEMORY_DIR="$HOME/clawd/memory"
MAX_DAILY_SIZE=5000  # bytes - warn if daily file exceeds this
MAX_MEMORY_SIZE=3000 # bytes - warn if MEMORY.md exceeds this

echo "=== Memory Hygiene Check ==="
echo "Time: $(date)"
echo ""

# 1. Check for fragment files (timestamped files like 2026-02-01-0507.md)
echo "Checking for fragments..."
FRAGMENTS=$(find "$MEMORY_DIR" -name "????-??-??-*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$FRAGMENTS" -gt 0 ]; then
    echo "⚠️  FOUND $FRAGMENTS fragment files - need consolidation:"
    find "$MEMORY_DIR" -name "????-??-??-*.md" -exec basename {} \;
    echo ""
    echo "Run: cat $MEMORY_DIR/YYYY-MM-DD-*.md >> $MEMORY_DIR/YYYY-MM-DD.md && rm $MEMORY_DIR/YYYY-MM-DD-*.md"
else
    echo "✅ No fragments found"
fi
echo ""

# 2. Check daily file sizes
echo "Checking daily file sizes..."
OVERSIZED=0
for f in "$MEMORY_DIR"/????-??-??.md; do
    [ -f "$f" ] || continue
    SIZE=$(wc -c < "$f" | tr -d ' ')
    NAME=$(basename "$f")
    if [ "$SIZE" -gt "$MAX_DAILY_SIZE" ]; then
        echo "⚠️  $NAME is ${SIZE}B (max: ${MAX_DAILY_SIZE}B) - needs trimming"
        OVERSIZED=$((OVERSIZED + 1))
    fi
done
if [ "$OVERSIZED" -eq 0 ]; then
    echo "✅ All daily files within limits"
fi
echo ""

# 3. Check MEMORY.md size
echo "Checking MEMORY.md..."
if [ -f "$HOME/clawd/MEMORY.md" ]; then
    MEM_SIZE=$(wc -c < "$HOME/clawd/MEMORY.md" | tr -d ' ')
    if [ "$MEM_SIZE" -gt "$MAX_MEMORY_SIZE" ]; then
        echo "⚠️  MEMORY.md is ${MEM_SIZE}B (max: ${MAX_MEMORY_SIZE}B) - review for redundancy"
    else
        echo "✅ MEMORY.md is ${MEM_SIZE}B (within limit)"
    fi
fi
echo ""

# 4. Count total memory files
TOTAL_FILES=$(find "$MEMORY_DIR" -name "*.md" | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$MEMORY_DIR" 2>/dev/null | cut -f1)
echo "Summary: $TOTAL_FILES files, $TOTAL_SIZE total"
echo ""

# 5. Quick health score
ISSUES=$((FRAGMENTS + OVERSIZED))
if [ "$ISSUES" -eq 0 ]; then
    echo "🟢 HEALTHY - No issues found"
    exit 0
else
    echo "🟡 NEEDS ATTENTION - $ISSUES issue(s) found"
    exit 1
fi
