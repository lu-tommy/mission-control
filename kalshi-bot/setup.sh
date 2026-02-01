#!/bin/bash
# Kalshi Trading Bot Setup Script

set -e  # Exit on error

echo "🦞 Kalshi Trading Bot Setup"
echo "============================"

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

# Check if python3.11+ is available
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✗ Python 3.8+ required. Current: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "✓ Created .env file"
        echo "⚠️  IMPORTANT: Edit .env with your actual Kalshi API credentials"
    else
        echo "⚠️  Warning: .env.example not found"
    fi
else
    echo "✓ .env file already exists"
fi

# Check for credentials file
if [ ! -f "../kalshi-config.secret.json" ]; then
    echo ""
    echo "⚠️  WARNING: kalshi-config.secret.json not found in parent directory"
    echo "   The bot requires this file for API authentication."
    echo "   Create it with your Kalshi API credentials."
else
    echo "✓ Credentials file found"
fi

# Verify imports
echo ""
echo "Verifying Python imports..."
python -c "import jwt; import requests; import cryptography" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All dependencies imported successfully"
else
    echo "✗ Import verification failed"
    exit 1
fi

# Test bot initialization (without API calls)
echo ""
echo "Testing bot initialization..."
python -c "from trading_bot import TradingBot; print('✓ TradingBot initialized successfully')"

echo ""
echo "============================"
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your API credentials in ../kalshi-config.secret.json"
echo "2. (Optional) Configure bot settings in .env"
echo "3. Run the bot: python trading_bot.py"
echo "4. Or test connection: python kalshi_api.py"
