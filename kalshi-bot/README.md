# Kalshi Trading Bot

Automated trading bot for Kalshi prediction markets.

## Setup

```bash
# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Add your Kalshi credentials
# (Already configured in ../kalshi-config.secret.json)
```

## Usage

```bash
# Run the bot
python3 bot.py

# Test connection
python3 test_connection.py

# View available markets
python3 list_markets.py
```

## Security

- Credentials stored in `../kalshi-config.secret.json` (gitignored)
- Never commit `.secret.json` files
- Use read-only API calls for testing first
