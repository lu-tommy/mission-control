#!/usr/bin/env python3
"""
List available Kalshi markets
Useful for browsing and finding trading opportunities
"""

from typing import Any, Dict

from kalshi_api import KalshiClient, KalshiConfigError, KalshiAPIError


# Display constants
DEFAULT_LIMIT = 20  # Default number of markets to display
DEFAULT_MIN_VOLUME = 0  # Default minimum volume threshold


def list_markets(limit: int = DEFAULT_LIMIT, min_volume: int = DEFAULT_MIN_VOLUME) -> None:
    """
    List and display available Kalshi markets.

    Args:
        limit: Maximum number of markets to fetch and display
        min_volume: Minimum volume threshold for showing detailed pricing
    """
    print("📊 Kalshi Markets")
    print("=" * 80)

    try:
        client: KalshiClient = KalshiClient()

        print(f"\nFetching markets (limit: {limit})...")
        response: Dict[str, Any] = client.get_markets(limit=limit, status='open')

        markets = response.get('markets', [])

        if not markets:
            print("No markets found.")
            return

        print(f"\nFound {len(markets)} open markets:\n")

        for i, market in enumerate(markets, 1):
            title = market.get('title', 'N/A')
            market_id = market.get('market_id', 'N/A')
            volume = market.get('volume', 0)
            close_time = market.get('close_time', 'N/A')

            # Format volume
            volume_str = f"${volume:,.0f}" if volume > 0 else "No volume"

            print(f"{i}. {title}")
            print(f"   ID: {market_id}")
            print(f"   Volume: {volume_str}")
            print(f"   Closes: {close_time}")

            # Get detailed info for liquid markets
            if volume > min_volume:
                try:
                    details: Dict[str, Any] = client.get_market(market_id)
                    yes_bid = details.get('yes_bid', '-')
                    yes_ask = details.get('yes_ask', '-')
                    no_bid = details.get('no_bid', '-')
                    no_ask = details.get('no_ask', '-')

                    print(f"   Yes Bid/Ask: {yes_bid}¢ / {yes_ask}¢")
                    print(f"   No Bid/Ask:  {no_bid}¢ / {no_ask}¢")
                except (KalshiAPIError, KeyError):
                    # Continue if we can't get details for this market
                    pass

            print()

        print("=" * 80)

    except (KalshiConfigError, KalshiAPIError) as e:
        print(f"\n✗ API Error: {e}")
        print("\nMake sure kalshi-config.secret.json is properly configured.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        print("\nMake sure kalshi-config.secret.json is properly configured.")


if __name__ == "__main__":
    import sys

    # Parse command line args
    limit = DEFAULT_LIMIT
    min_volume = DEFAULT_MIN_VOLUME

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("Usage: python list_markets.py [limit] [min_volume]")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            min_volume = int(sys.argv[2])
        except ValueError:
            print("Usage: python list_markets.py [limit] [min_volume]")
            sys.exit(1)

    list_markets(limit=limit, min_volume=min_volume)
