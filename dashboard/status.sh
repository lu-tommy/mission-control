#!/bin/bash

echo "🦞 Larry Dashboard Status"
echo "=========================="
echo ""

# Check container status
STATUS=$(docker ps -a --filter name=larry-dashboard --format "{{.Status}}")
echo "Container Status: $STATUS"

# Check if running
if docker ps --filter name=larry-dashboard --format "{{.Names}}" | grep -q larry-dashboard; then
    echo "✅ Dashboard is RUNNING"
    echo ""
    echo "Access at: http://localhost:8888"
    echo ""
    # Check recent logs
    echo "Recent logs (last 5 lines):"
    docker logs --tail 5 larry-dashboard
else
    echo "❌ Dashboard is NOT running"
fi

echo ""
echo "=========================="
