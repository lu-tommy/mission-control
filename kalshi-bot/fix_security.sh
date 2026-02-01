#!/bin/bash
#
# Kalshi Trading Bot - Security Remediation Script
# Fixes CRITICAL security issues identified in audit
#
# Run: ./fix_security.sh
#

set -e

echo "=========================================="
echo "Kalshi Bot Security Remediation"
echo "=========================================="
echo ""

# Check we're in the right directory
if [ ! -f "kalshi_api.py" ]; then
    echo "ERROR: Run this script from the kalshi-bot directory"
    exit 1
fi

echo "🔒 Fixing credential file permissions..."
echo ""

# Fix kalshi-config.secret.json (parent directory)
CREDENTIALS_FILE="../kalshi-config.secret.json"
if [ -f "$CREDENTIALS_FILE" ]; then
    echo "Found: $CREDENTIALS_FILE"
    chmod 600 "$CREDENTIALS_FILE"
    echo "  ✅ Fixed: permissions set to 600 (rw-------)"
    ls -la "$CREDENTIALS_FILE"
else
    echo "  ⚠️  Not found: $CREDENTIALS_FILE"
fi

echo ""

# Fix .env file
if [ -f ".env" ]; then
    echo "Found: .env"
    chmod 600 .env
    echo "  ✅ Fixed: permissions set to 600 (rw-------)"
    ls -la .env
else
    echo "  ⚠️  Not found: .env"
fi

echo ""
echo "=========================================="
echo "Security Fixes Applied"
echo "=========================================="
echo ""
echo "✅ Credential file permissions fixed"
echo ""
echo "⚠️  MANUAL ACTION REQUIRED:"
echo "   The bot does NOT have paper trading mode."
echo "   Running it will place REAL trades immediately."
echo ""
echo "   BEFORE running the bot:"
echo "   1. Add paper trading mode (see SECURITY_AUDIT_REPORT.md)"
echo "   2. Add confirmation prompt for live trades"
echo "   3. Test thoroughly in simulation mode"
echo ""
echo "See: SECURITY_AUDIT_REPORT.md for full details"
echo ""
