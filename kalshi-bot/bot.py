#!/usr/bin/env python3
"""
Simple wrapper to run the trading bot
This is a convenience script matching the README documentation
"""

from trading_bot import TradingBot


def main() -> None:
    """
    Main entry point for the Kalshi trading bot.

    Runs the bot in single-run mode by default. For continuous operation,
    modify this file to call bot.run() instead of bot.run_once().
    """
    print("🦞 Kalshi Trading Bot")
    print("=" * 60)
    print("Mode: Single run (edit trading_bot.py for continuous mode)")
    print("=" * 60)
    print()

    bot: TradingBot = TradingBot()

    # Run single iteration by default
    # To run continuously, uncomment: bot.run()
    bot.run_once()

    print()
    print("Done! To run continuously, edit trading_bot.py and call bot.run()")


if __name__ == "__main__":
    main()
