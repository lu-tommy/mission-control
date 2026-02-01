"""
Kalshi Trading Bot - Liquidity Provider Strategy
Places orders on both sides of the market to capture bid-ask spread
"""

import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from kalshi_api import KalshiClient, KalshiAPIError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, client: Optional[KalshiClient] = None):
        """
        Initialize trading bot

        Args:
            client: Optional KalshiClient instance. If None, creates new instance.
        """
        self.client = client or KalshiClient()
        self.state_file = Path(__file__).parent / "bot_state.json"
        self.state: Dict[str, Any] = {}
        self.load_state()
        logger.info("TradingBot initialized")

    def load_state(self) -> None:
        """Load persistent bot state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                logger.info(f"Loaded state from {self.state_file}")
            else:
                self.state = {
                    'last_check': None,
                    'tracked_markets': {},
                    'total_trades': 0,
                    'total_profit': 0
                }
                logger.info("Initialized new state")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid state file JSON: {e}. Using default state.")
            self.state = {
                'last_check': None,
                'tracked_markets': {},
                'total_trades': 0,
                'total_profit': 0
            }
        except Exception as e:
            logger.error(f"Error loading state: {e}. Using default state.")
            self.state = {
                'last_check': None,
                'tracked_markets': {},
                'total_trades': 0,
                'total_profit': 0
            }

    def save_state(self) -> None:
        """Save bot state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def log(self, message: str) -> None:
        """
        Log with timestamp (legacy method for compatibility)

        Args:
            message: Message to log
        """
        logger.info(message)

    def get_liquid_markets(self) -> List[Dict[str, Any]]:
        """
        Find markets with good liquidity

        Returns:
            List of liquid market dictionaries
        """
        self.log("Scanning for liquid markets...")

        try:
            markets_response = self.client.get_markets(limit=100, status='open')

            # Validate response structure
            if not markets_response:
                logger.warning("get_liquid_markets: Empty response from get_markets")
                return []

            markets = markets_response.get('markets', [])

            if not markets:
                logger.warning("get_liquid_markets: No markets in response")
                return []

            liquid = []

            for market in markets:
                # Validate market has required fields
                if not isinstance(market, dict):
                    continue

                market_id = market.get('market_id')
                if not market_id:
                    continue

                try:
                    details = self.client.get_market(market_id)

                    # Validate details response
                    if not details:
                        logger.debug(f"Market {market_id}: Empty details response")
                        continue

                    # Check liquidity indicators
                    volume = details.get('volume', 0)
                    close_time = details.get('close_time', '')

                    # Only trade liquid markets with time remaining
                    if volume > 1000:  # Minimum volume threshold
                        liquid.append({
                            'id': market_id,
                            'title': market.get('title', 'Unknown'),
                            'volume': volume,
                            'yes_bid': details.get('yes_bid', 0),
                            'yes_ask': details.get('yes_ask', 0),
                            'no_bid': details.get('no_bid', 0),
                            'no_ask': details.get('no_ask', 0),
                            'close_time': close_time
                        })

                except KalshiAPIError as e:
                    logger.debug(f"Error fetching market {market_id}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Unexpected error for market {market_id}: {e}")
                    continue

            # Sort by volume (descending)
            liquid.sort(key=lambda x: x.get('volume', 0), reverse=True)

            self.log(f"Found {len(liquid)} liquid markets")
            return liquid[:10]  # Top 10

        except KalshiAPIError as e:
            logger.error(f"API error scanning markets: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scanning markets: {e}")
            return []

    def calculate_spread(self, market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate bid-ask spread opportunity

        Args:
            market: Market dictionary with bid/ask data

        Returns:
            Opportunity dictionary if profitable, None otherwise
        """
        # Validate input
        if not market or not isinstance(market, dict):
            return None

        yes_bid = market.get('yes_bid', 0)
        yes_ask = market.get('yes_ask', 0)
        no_bid = market.get('no_bid', 0)
        no_ask = market.get('no_ask', 0)

        # Validate bid/ask values
        if not all(isinstance(x, (int, float)) for x in [yes_bid, yes_ask, no_bid, no_ask]):
            logger.warning(f"Invalid bid/ask values for market {market.get('id', 'unknown')}")
            return None

        # Calculate spread in cents
        if yes_bid and yes_ask:
            spread = yes_ask - yes_bid

            # Profitable if spread >= 2 cents
            if spread >= 2:
                return {
                    'type': 'yes',
                    'buy_price': yes_bid,
                    'sell_price': yes_ask,
                    'spread': spread,
                    'profit_pct': (spread / yes_bid) * 100 if yes_bid > 0 else 0
                }

        if no_bid and no_ask:
            spread = no_ask - no_bid

            if spread >= 2:
                return {
                    'type': 'no',
                    'buy_price': no_bid,
                    'sell_price': no_ask,
                    'spread': spread,
                    'profit_pct': (spread / no_bid) * 100 if no_bid > 0 else 0
                }

        return None

    def place_market_making_orders(self, market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Place orders on both sides to capture spread

        Args:
            market: Market dictionary

        Returns:
            Result dictionary with orders and expected profit, or None if failed
        """
        title = market.get('title', 'Unknown')[:50]
        self.log(f"Analyzing {title}...")

        opportunity = self.calculate_spread(market)

        if not opportunity:
            return None

        self.log(f"  Opportunity found: {opportunity['spread']}¢ spread ({opportunity['profit_pct']:.2f}%)")

        # Small position size for risk management
        position_size = 10  # 10 contracts

        orders = []

        try:
            # Place buy order at bid
            buy_order = self.client.place_order(
                market_id=market['id'],
                side=opportunity['type'],
                price=opportunity['buy_price'] + 1,  # Slightly above bid
                count=position_size,
                order_type='limit'
            )

            # Validate order response
            if not buy_order:
                logger.error("Buy order returned empty response")
                return None

            order_id = buy_order.get('order_id')
            if not order_id:
                logger.error(f"Buy order response missing order_id: {buy_order}")
                return None

            orders.append(buy_order)
            self.log(f"  ✓ Buy order placed: {position_size} @ {opportunity['buy_price'] + 1}¢")

            # Place sell order at ask
            sell_order = self.client.place_order(
                market_id=market['id'],
                side='yes' if opportunity['type'] == 'no' else 'no',
                price=100 - (opportunity['sell_price'] - 1),  # Convert to opposite side
                count=position_size,
                order_type='limit'
            )

            # Validate order response
            if not sell_order:
                logger.error("Sell order returned empty response")
                # Cancel the buy order since we can't complete the pair
                try:
                    self.client.cancel_order(order_id)
                    logger.info("Cancelled buy order due to sell order failure")
                except:
                    pass
                return None

            sell_order_id = sell_order.get('order_id')
            if not sell_order_id:
                logger.error(f"Sell order response missing order_id: {sell_order}")
                # Cancel the buy order since we can't complete the pair
                try:
                    self.client.cancel_order(order_id)
                    logger.info("Cancelled buy order due to sell order failure")
                except:
                    pass
                return None

            orders.append(sell_order)
            self.log(f"  ✓ Sell order placed: {position_size} @ {opportunity['sell_price'] - 1}¢")

            return {
                'market_id': market['id'],
                'orders': orders,
                'expected_profit': opportunity['spread'] * position_size
            }

        except KalshiAPIError as e:
            self.log(f"  ✗ Order failed (API error): {e}")
            # Cancel any orders that did go through
            for order in orders:
                try:
                    order_id = order.get('order_id')
                    if order_id:
                        self.client.cancel_order(order_id)
                except Exception as cancel_error:
                    logger.debug(f"Failed to cancel order: {cancel_error}")
            return None
        except ValueError as e:
            self.log(f"  ✗ Order failed (validation error): {e}")
            # Cancel any orders that did go through
            for order in orders:
                try:
                    order_id = order.get('order_id')
                    if order_id:
                        self.client.cancel_order(order_id)
                except Exception as cancel_error:
                    logger.debug(f"Failed to cancel order: {cancel_error}")
            return None
        except Exception as e:
            self.log(f"  ✗ Order failed (unexpected error): {e}")
            # Cancel any orders that did go through
            for order in orders:
                try:
                    order_id = order.get('order_id')
                    if order_id:
                        self.client.cancel_order(order_id)
                except Exception as cancel_error:
                    logger.debug(f"Failed to cancel order: {cancel_error}")
            return None

    def run_once(self) -> None:
        """Run one trading iteration"""
        self.log("=" * 60)
        self.log("Starting trading cycle...")

        try:
            # Get account balance
            balance = self.client.get_balance()

            # Validate balance response
            if not balance:
                logger.warning("Failed to get balance - using default")
                cash = 0
            else:
                cash = balance.get('cash', 0) / 100  # Convert to dollars

            self.log(f"Account balance: ${cash:.2f}")

            # Find liquid markets
            markets = self.get_liquid_markets()

            if not markets:
                self.log("No liquid markets found")
                return

            # Try to place orders on best markets
            profits = []

            for market in markets[:5]:  # Top 5 markets
                result = self.place_market_making_orders(market)
                if result:
                    profits.append(result['expected_profit'])

                # Small delay between orders
                time.sleep(1)

            # Summary
            if profits:
                total_expected = sum(profits)
                self.log(f"\n✓ Placed orders with expected profit: ${total_expected / 100:.2f}")

                self.state['total_trades'] = self.state.get('total_trades', 0) + len(profits)
                self.save_state()

            else:
                self.log("No profitable opportunities found")

            # Update last check time
            self.state['last_check'] = datetime.now().isoformat()
            self.save_state()

        except KalshiAPIError as e:
            logger.error(f"API error in trading cycle: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in trading cycle: {e}")

    def run(self) -> None:
        """Run bot continuously"""
        self.log("🦞 Kalshi Trading Bot Starting...")
        self.log("=" * 60)

        while True:
            try:
                self.run_once()

                # Wait 5 minutes between cycles
                self.log("\nWaiting 5 minutes...")
                time.sleep(300)

            except KeyboardInterrupt:
                self.log("\nBot stopped by user")
                break
            except Exception as e:
                logger.error(f"Fatal error in continuous loop: {e}")
                time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    bot = TradingBot()

    # Run once for testing
    print("Running single trading cycle...")
    bot.run_once()

    # Uncomment for continuous operation:
    # bot.run()
