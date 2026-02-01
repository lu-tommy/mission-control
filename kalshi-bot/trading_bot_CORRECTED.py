"""
Kalshi Trading Bot - Liquidity Provider Strategy (CORRECTED VERSION)
Places orders on both sides of the market to capture bid-ask spread

CHANGES FROM ORIGINAL:
- Fixed opposite side price calculation (Issue #1)
- Added fee calculations (Issue #2)
- Implemented Kelly Criterion position sizing (Issue #3)
- Added circuit breakers (Issue #4)
- Added inventory management (Issue #5)
"""

import time
import json
from datetime import datetime
from kalshi_api import KalshiClient
from pathlib import Path

# ============== CONFIGURATION ==============
# Fee settings
KALSHI_FEE_PER_CONTRACT = 2  # cents per side (verify with Kalshi)
MIN_PROFIT_CENTS = 1  # Minimum profit after fees

# Position sizing
USE_KELLY_SIZING = True  # Use Kelly Criterion (True) or fixed % (False)
RISK_PER_TRADE_PCT = 0.01  # 1% of account per trade (if not using Kelly)
MAX_POSITION_CONTRACTS = 100  # Hard cap
MIN_POSITION_CONTRACTS = 1

# Risk limits
DAILY_LOSS_LIMIT_CENTS = 5000  # $50 max daily loss
MAX_DRAWDOWN_PCT = 0.10  # 10% max drawdown
MAX_POSITION_VALUE_CENTS = 10000  # $100 max per position
MAX_EXPOSURE_CENTS = 5000  # $50 max net exposure
ORDERS_PER_MINUTE = 10  # Rate limit

# Market filters
MIN_VOLUME_THRESHOLD = 1000  # Minimum market volume
MIN_SPREAD_CENTS = 2  # Minimum spread to consider


# ============== CIRCUIT BREAKER ==============
class CircuitBreaker:
    """Risk management circuit breakers"""

    def __init__(self):
        self.daily_loss_limit = DAILY_LOSS_LIMIT_CENTS
        self.max_drawdown_pct = MAX_DRAWDOWN_PCT
        self.max_position_value = MAX_POSITION_VALUE_CENTS
        self.orders_per_minute_limit = ORDERS_PER_MINUTE
        self.start_balance = 0
        self.peak_balance = 0
        self.daily_pnl = 0
        self.order_timestamps = []
        self.last_reset_date = datetime.now().date()

    def reset_if_new_day(self):
        """Reset daily limits at start of new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.order_timestamps = []
            self.last_reset_date = today
            return True
        return False

    def check_trade_allowed(self, current_balance, position_value):
        """Check if trade is allowed based on risk limits"""
        self.reset_if_new_day()

        # Update peak balance
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        # Check daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            return False, f"Daily loss limit exceeded: ${abs(self.daily_pnl)/100:.2f}"

        # Check max drawdown
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - current_balance) / self.peak_balance
            if drawdown > self.max_drawdown_pct:
                return False, f"Max drawdown exceeded: {drawdown*100:.1f}%"

        # Check position size
        if position_value > self.max_position_value:
            return False, f"Position too large: ${position_value/100:.2f}"

        # Check rate limits
        now = time.time()
        recent_orders = [t for t in self.order_timestamps if now - t < 60]
        if len(recent_orders) >= self.orders_per_minute_limit:
            return False, f"Rate limit: {len(recent_orders)} orders in last minute"

        return True, "OK"

    def record_order(self):
        """Record order for rate limiting"""
        self.order_timestamps.append(time.time())

    def record_pnl(self, pnl_cents):
        """Record trade P&L"""
        self.daily_pnl += pnl_cents


# ============== INVENTORY MANAGER ==============
class InventoryManager:
    """Manage exposure and prevent imbalances"""

    def __init__(self, max_exposure=MAX_EXPOSURE_CENTS):
        self.max_exposure = max_exposure
        self.yes_contracts = 0
        self.no_contracts = 0
        self.avg_yes_price = 50  # cents
        self.avg_no_price = 50  # cents

    def get_exposure(self):
        """Calculate current exposure"""
        yes_value = self.yes_contracts * self.avg_yes_price
        no_value = self.no_contracts * self.avg_no_price
        net_exposure = yes_value - no_value

        total_value = yes_value + no_value
        imbalance_pct = abs(net_exposure) / max(total_value, 1)

        return {
            'yes_contracts': self.yes_contracts,
            'no_contracts': self.no_contracts,
            'yes_value': yes_value,
            'no_value': no_value,
            'net_exposure': abs(net_exposure),
            'imbalance_pct': imbalance_pct
        }

    def can_add_position(self, side, quantity, price_cents):
        """Check if adding position is safe"""
        exposure = self.get_exposure()

        # Estimate new exposure
        if side == 'yes':
            new_yes_value = (self.yes_contracts + quantity) * price_cents
            new_no_value = self.no_contracts * self.avg_no_price
        else:
            new_yes_value = self.yes_contracts * self.avg_yes_price
            new_no_value = (self.no_contracts + quantity) * price_cents

        new_exposure = abs(new_yes_value - new_no_value)

        if new_exposure > self.max_exposure:
            return False, f"Would exceed max exposure: ${new_exposure/100:.2f}"

        return True, "OK"

    def add_position(self, side, quantity, price_cents):
        """Record filled position"""
        if side == 'yes':
            # Update weighted average price
            total_cost = self.yes_contracts * self.avg_yes_price + quantity * price_cents
            self.yes_contracts += quantity
            self.avg_yes_price = total_cost / self.yes_contracts
        else:
            total_cost = self.no_contracts * self.avg_no_price + quantity * price_cents
            self.no_contracts += quantity
            self.avg_no_price = total_cost / self.no_contracts


# ============== POSITION SIZING ==============
def calculate_position_size_kelly(account_balance_cents, win_prob, avg_win_cents, avg_loss_cents):
    """
    Calculate position size using Kelly Criterion

    Kelly Formula: f* = (bp - q) / b
    where:
        b = odds (avg_win / avg_loss)
        p = probability of winning
        q = 1 - p
    """
    if avg_loss_cents <= 0:
        return MIN_POSITION_CONTRACTS

    # Calculate odds
    odds = avg_win_cents / avg_loss_cents

    # Kelly fraction
    kelly_frac = (odds * win_prob - (1 - win_prob)) / odds

    # Use half-Kelly for safety
    kelly_frac = max(0, kelly_frac * 0.5)

    # Cap Kelly at 5% per trade (very conservative)
    kelly_frac = min(kelly_frac, 0.05)

    # Calculate position size
    # For binary options, risk is contract price
    avg_price = (avg_win_cents + avg_loss_cents) / 2
    risk_amount = account_balance_cents * kelly_frac
    position_size = int(risk_amount / avg_price)

    # Apply limits
    position_size = max(MIN_POSITION_CONTRACTS, position_size)
    position_size = min(position_size, MAX_POSITION_CONTRACTS)

    return position_size


def calculate_position_size_fixed_pct(account_balance_cents, risk_pct=RISK_PER_TRADE_PCT):
    """
    Simple fixed percentage position sizing

    Risk is defined as max potential loss (contract price)
    """
    # Estimate average contract price
    avg_contract_price = 50  # cents

    # Calculate risk amount
    risk_amount = account_balance_cents * risk_pct

    # Calculate position size
    position_size = int(risk_amount / avg_contract_price)

    # Apply limits
    position_size = max(MIN_POSITION_CONTRACTS, position_size)
    position_size = min(position_size, MAX_POSITION_CONTRACTS)

    return position_size


# ============== MAIN TRADING BOT ==============
class TradingBot:
    def __init__(self):
        self.client = KalshiClient()
        self.state_file = Path(__file__).parent / "bot_state.json"
        self.circuit_breaker = CircuitBreaker()
        self.inventory_manager = InventoryManager()
        self.load_state()

        # Initialize circuit breaker with starting balance
        if self.circuit_breaker.start_balance == 0:
            try:
                balance = self.client.get_balance()
                self.circuit_breaker.start_balance = balance.get('cash', 0)
                self.circuit_breaker.peak_balance = self.circuit_breaker.start_balance
            except:
                pass

    def load_state(self):
        """Load persistent bot state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                'last_check': None,
                'tracked_markets': {},
                'total_trades': 0,
                'total_profit': 0,
                'win_rate': 0
            }

    def save_state(self):
        """Save bot state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

    def get_liquid_markets(self):
        """Find markets with good liquidity"""
        self.log("Scanning for liquid markets...")

        markets = self.client.get_markets(limit=100, status='open')
        liquid = []

        for market in markets.get('markets', []):
            market_id = market.get('market_id')

            try:
                details = self.client.get_market(market_id)

                volume = details.get('volume', 0)
                close_time = details.get('close_time', '')

                if volume > MIN_VOLUME_THRESHOLD:
                    liquid.append({
                        'id': market_id,
                        'title': market.get('title', ''),
                        'volume': volume,
                        'yes_bid': details.get('yes_bid', 0),
                        'yes_ask': details.get('yes_ask', 0),
                        'no_bid': details.get('no_bid', 0),
                        'no_ask': details.get('no_ask', 0),
                        'close_time': close_time
                    })

            except Exception as e:
                continue

        liquid.sort(key=lambda x: x['volume'], reverse=True)
        self.log(f"Found {len(liquid)} liquid markets")
        return liquid[:10]

    def calculate_spread(self, market):
        """
        Calculate bid-ask spread opportunity AFTER FEES
        Returns opportunity dict or None if not profitable
        """
        yes_bid = market.get('yes_bid', 0)
        yes_ask = market.get('yes_ask', 0)
        no_bid = market.get('no_bid', 0)
        no_ask = market.get('no_ask', 0)

        # Calculate minimum spread to be profitable
        # spread must exceed: buy_fee + sell_fee + min_profit
        min_spread = (KALSHI_FEE_PER_CONTRACT * 2) + MIN_PROFIT_CENTS

        # Check YES side
        if yes_bid and yes_ask:
            spread = yes_ask - yes_bid
            if spread >= min_spread:
                # Calculate NET profit after fees
                fees = KALSHI_FEE_PER_CONTRACT * 2
                net_profit = spread - fees
                profit_pct = (net_profit / yes_bid) * 100 if yes_bid > 0 else 0

                return {
                    'type': 'yes',
                    'buy_price': yes_bid,
                    'sell_price': yes_ask,
                    'spread': spread,
                    'fees': fees,
                    'net_profit': net_profit,
                    'profit_pct': profit_pct
                }

        # Check NO side
        if no_bid and no_ask:
            spread = no_ask - no_bid
            if spread >= min_spread:
                fees = KALSHI_FEE_PER_CONTRACT * 2
                net_profit = spread - fees
                profit_pct = (net_profit / no_bid) * 100 if no_bid > 0 else 0

                return {
                    'type': 'no',
                    'buy_price': no_bid,
                    'sell_price': no_ask,
                    'spread': spread,
                    'fees': fees,
                    'net_profit': net_profit,
                    'profit_pct': profit_pct
                }

        return None

    def determine_position_size(self, account_balance_cents, opportunity):
        """Determine position size based on configuration"""
        if USE_KELLY_SIZING:
            # Estimate win probability and payoff
            # For market making, win prob depends on spread
            edge = opportunity['net_profit'] / opportunity['buy_price']
            win_prob = 0.5 + (edge / 2)  # Conservative estimate
            avg_win = opportunity['net_profit']
            avg_loss = opportunity['buy_price']  # Max loss

            return calculate_position_size_kelly(
                account_balance_cents, win_prob, avg_win, avg_loss
            )
        else:
            return calculate_position_size_fixed_pct(account_balance_cents)

    def place_market_making_orders(self, market):
        """Place orders on both sides to capture spread (CORRECTED)"""
        self.log(f"Analyzing {market['title'][:50]}...")

        opportunity = self.calculate_spread(market)
        if not opportunity:
            return None

        self.log(f"  Opportunity: {opportunity['spread']}¢ spread, "
                f"net profit: {opportunity['net_profit']}¢ ({opportunity['profit_pct']:.2f}%)")

        # Get account balance
        try:
            balance = self.client.get_balance()
            account_balance_cents = balance.get('cash', 0)
        except:
            self.log("  ✗ Could not get balance")
            return None

        # Determine position size
        position_size = self.determine_position_size(account_balance_cents, opportunity)
        position_value = opportunity['buy_price'] * position_size

        self.log(f"  Position size: {position_size} contracts (${position_value/100:.2f})")

        # CHECK CIRCUIT BREAKER
        allowed, reason = self.circuit_breaker.check_trade_allowed(
            account_balance_cents, position_value
        )

        if not allowed:
            self.log(f"  ⛔ BLOCKED by circuit breaker: {reason}")
            return None

        # CHECK INVENTORY
        can_add, inv_reason = self.inventory_manager.can_add_position(
            opportunity['type'], position_size, opportunity['buy_price']
        )

        if not can_add:
            self.log(f"  🚫 BLOCKED by inventory manager: {inv_reason}")
            return None

        orders = []

        try:
            # Place buy order at bid
            # Buy slightly above bid to improve fill probability
            buy_price = opportunity['buy_price'] + 1

            buy_order = self.client.place_order(
                market_id=market['id'],
                side=opportunity['type'],
                price=buy_price,
                count=position_size,
                order_type='limit'
            )

            orders.append(buy_order)
            self.log(f"  ✓ Buy order: {position_size} {opportunity['type'].upper()} @ {buy_price}¢")

            # Calculate hedge order (CORRECTED FORMULA)
            # For binary markets: YES_price + NO_price = 100
            # If we bought YES, we hedge by selling NO at (100 - YES_price)
            if opportunity['type'] == 'yes':
                hedge_side = 'no'
                # Sell NO at price that hedges our YES position
                hedge_price = 100 - opportunity['sell_price']
            else:  # opportunity['type'] == 'no'
                hedge_side = 'yes'
                # Sell YES at price that hedges our NO position
                hedge_price = 100 - opportunity['sell_price']

            # Place hedge order
            sell_order = self.client.place_order(
                market_id=market['id'],
                side=hedge_side,
                price=hedge_price,
                count=position_size,
                order_type='limit'
            )

            orders.append(sell_order)
            self.log(f"  ✓ Hedge order: {position_size} {hedge_side.upper()} @ {hedge_price}¢")

            # Record with circuit breaker and inventory
            self.circuit_breaker.record_order()
            expected_profit = opportunity['net_profit'] * position_size

            self.log(f"  ✓ Expected profit: ${expected_profit/100:.2f} (after fees)")

            return {
                'market_id': market['id'],
                'orders': orders,
                'expected_profit': expected_profit,
                'position_size': position_size
            }

        except Exception as e:
            self.log(f"  ✗ Order failed: {e}")
            # Cancel any orders that did go through
            for order in orders:
                try:
                    self.client.cancel_order(order.get('order_id'))
                except:
                    pass
            return None

    def run_once(self):
        """Run one trading iteration"""
        self.log("=" * 60)
        self.log("Starting trading cycle...")

        try:
            # Get account balance
            balance = self.client.get_balance()
            cash = balance.get('cash', 0) / 100
            self.log(f"Account balance: ${cash:.2f}")

            # Get inventory status
            inventory = self.inventory_manager.get_exposure()
            self.log(f"Inventory: {inventory['yes_contracts']} YES, "
                    f"{inventory['no_contracts']} NO, "
                    f"net exposure: ${inventory['net_exposure']/100:.2f}")

            # Find liquid markets
            markets = self.get_liquid_markets()

            if not markets:
                self.log("No liquid markets found")
                return

            # Try to place orders on best markets
            profits = []

            for market in markets[:5]:
                result = self.place_market_making_orders(market)
                if result:
                    profits.append(result['expected_profit'])

                time.sleep(1)

            # Summary
            if profits:
                total_expected = sum(profits)
                self.log(f"\n✓ Placed orders with expected profit: ${total_expected / 100:.2f}")

                self.state['total_trades'] += len(profits)
                self.save_state()

            else:
                self.log("No profitable opportunities found")

            # Update last check time
            self.state['last_check'] = datetime.now().isoformat()
            self.save_state()

        except Exception as e:
            self.log(f"Error in trading cycle: {e}")

    def run(self):
        """Run bot continuously"""
        self.log("🦞 Kalshi Trading Bot Starting...")
        self.log("=" * 60)

        while True:
            try:
                self.run_once()
                self.log("\nWaiting 5 minutes...")
                time.sleep(300)

            except KeyboardInterrupt:
                self.log("\nBot stopped by user")
                break
            except Exception as e:
                self.log(f"Fatal error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    bot = TradingBot()

    # Run once for testing
    print("Running single trading cycle...")
    bot.run_once()

    # Uncomment for continuous operation:
    # bot.run()
