#!/usr/bin/env python3
"""
Test Kalshi API connection
Verifies credentials and basic API functionality
"""

from typing import Any, Dict

from kalshi_api import KalshiClient, KalshiConfigError, KalshiAPIError


def test_connection() -> bool:
    """
    Test the Kalshi API connection and credentials.

    Returns:
        True if all tests pass, False otherwise
    """
    print("🔌 Testing Kalshi API Connection")
    print("=" * 60)

    try:
        client: KalshiClient = KalshiClient()
        print("✓ Credentials loaded successfully")

        # Test 1: Exchange status
        print("\n1. Checking exchange status...")
        status: Dict[str, Any] = client.get_exchange_status()
        print(f"   ✓ Exchange Status: {status.get('status', 'unknown')}")

        # Test 2: Get balance
        print("\n2. Checking account balance...")
        balance: Dict[str, Any] = client.get_balance()
        cash = balance.get('cash', 0) / 100  # Convert to dollars
        print(f"   ✓ Available Cash: ${cash:.2f}")

        # Test 3: List markets
        print("\n3. Fetching available markets...")
        markets: Dict[str, Any] = client.get_markets(limit=5)
        market_count = len(markets.get('markets', []))
        print(f"   ✓ Found {market_count} markets")

        # Show first market if available
        if market_count > 0:
            first_market = markets['markets'][0]
            print(f"   Example: {first_market.get('title', 'N/A')[:60]}...")

        # Test 4: Get portfolio
        print("\n4. Checking portfolio...")
        portfolio: Dict[str, Any] = client.get_portfolio()
        print(f"   ✓ Portfolio retrieved")

        print("\n" + "=" * 60)
        print("✅ All tests passed! API connection is working.")
        print("=" * 60)
        return True

    except FileNotFoundError as e:
        print(f"\n✗ Configuration file not found: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure kalshi-config.secret.json exists in parent directory")
        print("  2. Format should match the Kalshi API documentation")
        return False
    except (KalshiConfigError, KalshiAPIError) as e:
        print(f"\n✗ API Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API credentials in kalshi-config.secret.json")
        print("  2. Verify your account has API access enabled")
        print("  3. Check https://docs.kalshi.com for API status")
        print("  4. Ensure your API key has the required permissions")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API credentials in kalshi-config.secret.json")
        print("  2. Verify your account has API access enabled")
        print("  3. Check https://docs.kalshi.com for API status")
        print("  4. Ensure your API key has the required permissions")
        return False


if __name__ == "__main__":
    import sys

    success = test_connection()
    sys.exit(0 if success else 1)
