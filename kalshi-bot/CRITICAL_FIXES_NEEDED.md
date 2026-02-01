# Critical Fixes Needed - Code Analysis

**Document:** Detailed code issues with fixes
**Date:** 2025-01-30
**Status:** ACTION REQUIRED

---

## Issue #1: Incorrect Opposite Side Price Calculation

### Location: trading_bot.py, Line 113

### Current (WRONG) Code:
```python
# Place sell order at ask
sell_order = self.client.place_order(
    market_id=market['id'],
    side='yes' if opportunity['type'] == 'no' else 'no',
    price=100 - (opportunity['sell_price'] - 1),  # ❌ WRONG!
    count=position_size,
    order_type='limit'
)
```

### The Problem:
The formula `100 - (sell_price - 1)` is mathematically incorrect for binary options.

**Example:**
- Market: YES at 50¢
- If buying YES, the equivalent hedge is selling NO
- NO price should be: 100 - 50 = 50¢
- Code calculates: 100 - (50 - 1) = 51¢ ❌

This creates a **1¢ pricing error** on every trade.

### Fixed Code:
```python
# Place sell order at ask
# For binary markets: YES_price + NO_price = 100
# If buying YES at P, sell NO at (100 - P)
if opportunity['type'] == 'yes':
    hedge_side = 'no'
    hedge_price = 100 - opportunity['sell_price']
else:  # opportunity['type'] == 'no'
    hedge_side = 'yes'
    hedge_price = 100 - opportunity['sell_price']

sell_order = self.client.place_order(
    market_id=market['id'],
    side=hedge_side,
    price=hedge_price,
    count=position_size,
    order_type='limit'
)
```

### Impact:
- **Severity:** HIGH
- **Loss per trade:** 1¢ × position_size
- **Monthly impact (100 trades × 10 contracts):** $10 loss
- **Type:** Systematic error (always loses money)

---

## Issue #2: No Fee Calculations

### Location: trading_bot.py, Lines 79-91

### Current (WRONG) Code:
```python
def calculate_spread(self, market):
    """Calculate bid-ask spread opportunity"""
    yes_bid = market.get('yes_bid', 0)
    yes_ask = market.get('yes_ask', 0)

    if yes_bid and yes_ask:
        spread = yes_ask - yes_bid

        # Profitable if spread >= 2 cents
        if spread >= 2:  # ❌ IGNORES FEES!
            return {
                'spread': spread,
                'profit_pct': (spread / yes_bid) * 100
            }
```

### The Problem:
Kalshi charges fees on every trade. A 2¢ spread is NOT profitable after fees.

**Typical Kalshi Fees:**
- Maker fee: ~1¢ per contract
- Taker fee: ~2¢ per contract
- Round trip (buy + sell): ~4¢ per contract

**Example Trade:**
- Spread: 2¢
- Gross profit: 2¢ × 10 = 20¢
- Fees: 4¢ × 10 = 40¢
- **Net result: -20¢ LOSS**

### Fixed Code:
```python
# Fee configuration
KALSHI_FEE_PER_CONTRACT = 2  # cents, adjust based on actual fees
MIN_PROFIT_CENTS = 1  # Minimum profit after fees

def calculate_spread(self, market):
    """Calculate bid-ask spread opportunity AFTER FEES"""
    yes_bid = market.get('yes_bid', 0)
    yes_ask = market.get('yes_ask', 0)
    no_bid = market.get('no_bid', 0)
    no_ask = market.get('no_ask', 0)

    # Calculate required spread to be profitable
    # Need: spread > (buy_fee + sell_fee + min_profit)
    min_spread = (KALSHI_FEE_PER_CONTRACT * 2) + MIN_PROFIT_CENTS

    if yes_bid and yes_ask:
        spread = yes_ask - yes_bid

        # Only profitable if spread exceeds total fees
        if spread >= min_spread:
            net_profit_per_contract = spread - (KALSHI_FEE_PER_CONTRACT * 2)
            return {
                'type': 'yes',
                'buy_price': yes_bid,
                'sell_price': yes_ask,
                'spread': spread,
                'fees': KALSHI_FEE_PER_CONTRACT * 2,
                'net_profit': net_profit_per_contract,
                'profit_pct': (net_profit_per_contract / yes_bid) * 100 if yes_bid > 0 else 0
            }

    # Similar for NO side...
```

### Impact:
- **Severity:** CRITICAL
- **Current behavior:** Taking unprofitable trades
- **Loss per trade:** 2-4¢ per contract
- **Monthly impact:** Could lose 100% of capital

---

## Issue #3: Fixed Position Sizing

### Location: trading_bot.py, Line 95

### Current (RISKY) Code:
```python
# Small position size for risk management
position_size = 10  # 10 contracts ❌ IGNORES ACCOUNT SIZE!
```

### The Problem:
Fixed position sizing is dangerous. With a $100 account, 10 contracts at $1 each = 10% risk. With a $10,000 account, it's only 0.1% risk.

### Fixed Code (Kelly Criterion Approach):

```python
def calculate_position_size(self, account_balance, edge, volatility):
    """
    Calculate safe position size using Kelly Criterion

    Args:
        account_balance: Account balance in cents
        edge: Estimated edge (0.01 = 1%)
        volatility: Market volatility estimate

    Returns:
        Number of contracts to trade
    """
    # Conservative Kelly: use half-Kelly
    win_prob = 0.5 + edge  # Edge converts to win prob
    avg_win = 5  # cents
    avg_loss = 95  # cents (binary outcome)

    # Kelly fraction
    odds = avg_win / avg_loss
    kelly_frac = (odds * win_prob - (1 - win_prob)) / odds

    # Half-Kelly for safety
    kelly_frac = max(0, kelly_frac * 0.5)

    # Calculate position size
    risk_amount = account_balance * kelly_frac
    position_size = int(risk_amount / 100)  # $1 per contract

    # Hard limits
    MIN_POSITION = 1
    MAX_POSITION = 100
    MAX_PCT_OF_ACCOUNT = 0.02  # Max 2% per trade

    position_size = max(MIN_POSITION, position_size)
    position_size = min(position_size, MAX_POSITION)
    position_size = min(position_size, int(account_balance * MAX_PCT_OF_ACCOUNT / 100))

    return position_size
```

### Alternative (Fixed %):

```python
def calculate_position_size_simple(self, account_balance):
    """Simple fixed % position sizing"""
    RISK_PER_TRADE_PCT = 0.01  # 1% of account

    # For binary options, max loss is contract price
    # Assume avg contract price ~50¢
    avg_contract_value = 50  # cents

    risk_amount = account_balance * RISK_PER_TRADE_PCT
    position_size = int(risk_amount / avg_contract_value)

    return max(1, min(position_size, 100))  # 1-100 contracts
```

### Impact:
- **Severity:** HIGH
- **Small accounts:** Over-leveraged (could blow up)
- **Large accounts:** Under-leveraged (missing profit)
- **Proper sizing:** Balances risk vs. reward

---

## Issue #4: No Circuit Breakers

### Location: trading_bot.py - MISSING ENTIRELY

### Required Code:

Add this class to `trading_bot.py`:

```python
class CircuitBreaker:
    """Risk management circuit breakers"""

    def __init__(self):
        self.daily_loss_limit = 5000  # cents ($50)
        self.max_drawdown_pct = 0.10  # 10%
        self.max_position_size = 10000  # cents ($100)
        self.orders_per_minute_limit = 10
        self.start_balance = 0
        self.peak_balance = 0
        self.daily_pnl = 0
        self.order_timestamps = []

    def check_trade_allowed(self, current_balance, position_value):
        """Check if trade is allowed"""
        # Update peak
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        # Check daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            return False, "Daily loss limit exceeded"

        # Check max drawdown
        drawdown = (self.peak_balance - current_balance) / self.peak_balance
        if drawdown > self.max_drawdown_pct:
            return False, "Max drawdown exceeded"

        # Check position size
        if position_value > self.max_position_size:
            return False, "Position too large"

        # Check rate limits
        now = time.time()
        recent_orders = [t for t in self.order_timestamps if now - t < 60]
        if len(recent_orders) >= self.orders_per_minute_limit:
            return False, "Rate limit exceeded"

        return True, "OK"

    def record_order(self):
        """Record order for rate limiting"""
        self.order_timestamps.append(time.time())

    def record_pnl(self, pnl):
        """Record P&L"""
        self.daily_pnl += pnl

    def reset_daily(self):
        """Reset daily limits (call at start of day)"""
        self.daily_pnl = 0
        self.order_timestamps = []
```

### Integration in TradingBot:

```python
class TradingBot:
    def __init__(self):
        self.client = KalshiClient()
        self.circuit_breaker = CircuitBreaker()
        # ... existing code ...

    def place_market_making_orders(self, market):
        """Place orders with circuit breaker checks"""
        opportunity = self.calculate_spread(market)
        if not opportunity:
            return None

        # Get current balance
        balance = self.client.get_balance()
        current_balance = balance.get('cash', 0)

        # Calculate position value
        position_value = opportunity['buy_price'] * position_size

        # CHECK CIRCUIT BREAKER
        allowed, reason = self.circuit_breaker.check_trade_allowed(
            current_balance, position_value
        )

        if not allowed:
            self.log(f"⛔ BLOCKED: {reason}")
            return None

        # Proceed with order...
        self.circuit_breaker.record_order()
        # ... place orders ...
```

### Impact:
- **Severity:** HIGH
- **Prevents:** Catastrophic losses
- **Essential for:** Any live trading system

---

## Issue #5: Inventory Imbalance Risk

### Location: trading_bot.py - MISSING

### The Problem:
The bot could accumulate a large position on one side (e.g., lots of YES contracts) without corresponding NO hedges. If the market moves against you, losses compound.

### Required Code:

```python
class InventoryManager:
    """Manage exposure and prevent imbalances"""

    def __init__(self, max_exposure=5000):  # $50 max exposure
        self.max_exposure = max_exposure
        self.yes_contracts = 0
        self.no_contracts = 0

    def get_exposure(self):
        """Calculate current exposure"""
        yes_value = self.yes_contracts * 50  # Average price estimate
        no_value = self.no_contracts * 50
        net_exposure = yes_value - no_value
        return {
            'yes_value': yes_value,
            'no_value': no_value,
            'net_exposure': abs(net_exposure),
            'imbalance_pct': abs(net_exposure) / max(yes_value + no_value, 1)
        }

    def can_add_position(self, side, quantity):
        """Check if adding position is safe"""
        exposure = self.get_exposure()

        # Calculate new exposure
        if side == 'yes':
            new_yes = self.yes_contracts + quantity
            new_no = self.no_contracts
        else:
            new_yes = self.yes_contracts
            new_no = self.no_contracts + quantity

        new_exposure = abs((new_yes * 50) - (new_no * 50))

        if new_exposure > self.max_exposure:
            return False, f"Would exceed max exposure (${new_exposure/100:.2f})"

        return True, "OK"

    def add_position(self, side, quantity, filled_price):
        """Record filled position"""
        if side == 'yes':
            self.yes_contracts += quantity
        else:
            self.no_contracts += quantity
```

### Integration:

```python
def place_market_making_orders(self, market):
    """Place orders with inventory management"""
    # ... existing code ...

    # Check inventory before placing orders
    can_add, reason = self.inventory_manager.can_add_position(
        opportunity['type'], position_size
    )

    if not can_add:
        self.log(f"🚫 Inventory limit: {reason}")
        return None

    # Place order...
    # If filled:
    self.inventory_manager.add_position(side, quantity, price)
```

### Impact:
- **Severity:** MEDIUM-HIGH
- **Prevents:** Getting stuck on one side
- **Reduces:** Directional risk

---

## Summary of Required Changes

| Issue | File | Lines | Severity | Fix Time |
|-------|------|-------|----------|----------|
| #1 Price calculation | trading_bot.py | 113 | HIGH | 5 min |
| #2 Fee calculation | trading_bot.py | 79-91 | CRITICAL | 10 min |
| #3 Position sizing | trading_bot.py | 95 | HIGH | 15 min |
| #4 Circuit breakers | trading_bot.py | NEW | HIGH | 30 min |
| #5 Inventory mgmt | trading_bot.py | NEW | MEDIUM | 20 min |

**Total Estimated Fix Time:** 80 minutes

---

## Testing Checklist

After implementing fixes, verify:

- [ ] Price conversion: YES 50¢ → NO 50¢ (not 51¢)
- [ ] Fee calculation: 2¢ spread = rejected (not accepted)
- [ ] Position sizing: $100 account → 1-2 contracts (not 10)
- [ ] Circuit breaker: Blocks trade after $50 daily loss
- [ ] Inventory: Blocks trade if exposure > $50
- [ ] Backtest: Run 1000 trades, check P&L
- [ ] Paper trade: Test with real market data for 1 week

---

**Do NOT deploy to production until all fixes are complete and tested.**
