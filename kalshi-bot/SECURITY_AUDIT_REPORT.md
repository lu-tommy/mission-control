# Kalshi Trading Bot - Security Audit Report

**Date:** 2025-01-30  
**Auditor:** Subagent (kalshi-review-security)  
**Time Limit:** 15 minutes  
**Status:** 🔴 CRITICAL ISSUES FOUND

---

## Executive Summary

**SECURITY GRADE: D** (Critical vulnerabilities requiring immediate attention)

The Kalshi trading bot has **CRITICAL SECURITY VULNERABILITIES** that must be addressed before any live deployment. The most severe issues are:

1. **NO PAPER TRADING MODE** - Bot will place REAL trades immediately upon execution
2. **Credentials stored with 644 permissions** - Readable by all users on the system
3. **No encryption for state files** - Trading history stored in plain text
4. **Misleading .env file** - Unused credentials file creates false security

---

## 1. Credential Storage & Protection

### 🔴 CRITICAL: Insecure File Permissions

**Issue:** API credentials file has overly permissive access

**File:** `/Users/tommylu/clawd/kalshi-config.secret.json`
- **Current permissions:** `644` (rw-r--r--)
- **Owner:** tommylu:staff
- **Problem:** Readable by ALL users on the system
- **Should be:** `600` (rw-------)

**Content:**
```json
{
  "api_key_id": "<actual_key>",
  "private_key": "-----BEGIN PRIVATE KEY-----\n<actual_key>\n-----END PRIVATE KEY-----"
}
```

**Risk:** Any user with access to this machine can read the API credentials and place trades on your behalf.

**Remediation:**
```bash
chmod 600 /Users/tommylu/clawd/kalshi-config.secret.json
```

---

### 🟡 MEDIUM: Misleading .env File

**Issue:** The bot has a `.env` file but **does not use it**

**File:** `/Users/tommylu/clawd/kalshi-bot/.env`
- **Permissions:** `644` (also too permissive)
- **Status:** Created but **completely ignored by code**
- **Actual credentials:** Loaded from `../kalshi-config.secret.json` instead

**Code analysis:**
```python
# kalshi_api.py line 11
CONFIG_PATH = Path(__file__).parent.parent / "kalshi-config.secret.json"
```

**Risk:** Creates false sense of security. Users may think they're securing credentials in .env when they're actually in a different location.

**Remediation:**
1. Either load credentials from .env using python-dotenv
2. OR remove .env entirely and document the actual credentials location
3. OR secure both files with proper permissions

---

### ✅ GOOD: No Hardcoded Secrets in Code

**Finding:** No API keys, passwords, or tokens hardcoded in Python files

**Verification:**
```bash
grep -rn "api_key\|private_key" *.py | grep -v "\.secret\.json" | grep -v "#"
```
Only variable names found, no actual credentials.

---

## 2. Paper Trading Safeguards

### 🔴 CRITICAL: NO PAPER TRADING MODE

**Issue:** Bot has **NO simulation/dry-run mode** and will place REAL trades immediately

**Files checked:**
- `trading_bot.py` - No paper trading flag
- `kalshi_api.py` - No simulation mode
- `bot.py` - No safety checks

**Code analysis:**
```python
# trading_bot.py line 142-154 - Direct order placement with no check
buy_order = self.client.place_order(
    market_id=market['id'],
    side=opportunity['type'],
    price=opportunity['buy_price'] + 1,
    count=position_size,
    order_type='limit'
)
```

**Risk:** Running `python bot.py` will **immediately place real orders** with real money.

**Remediation:**
```python
# Add to TradingBot.__init__:
self.paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'

# Add to place_market_making_orders():
if self.paper_trading:
    self.log(f"  [PAPER TRADE] Would buy: {position_size} @ {price}¢")
    return simulated_order
else:
    return self.client.place_order(...)
```

---

### 🔴 CRITICAL: No Confirmation Before Trading

**Issue:** No "Are you sure?" prompt or manual approval step

**Finding:** The bot executes trades autonomously without any confirmation.

**Risk:** Accidental execution could result in immediate financial loss.

**Remediation:** Add confirmation prompt or require explicit `--live` flag:

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Actually place trades')
    args = parser.parse_args()
    
    if not args.live:
        print("DRY RUN MODE - No trades will be placed")
    else:
        response = input("CONFIRM: This will place REAL trades. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
```

---

## 3. Data Security

### 🟡 MEDIUM: Unencrypted State Files

**File:** `/Users/tommylu/clawd/kalshi-bot/bot_state.json` (when created)
- **Storage format:** Plain text JSON
- **Contents:** Trade history, positions, profit tracking
- **Permissions:** Will inherit from umask (likely 644)

**Example state data:**
```json
{
  "last_check": "2025-01-30T...",
  "tracked_markets": {...},
  "total_trades": 42,
  "total_profit": 1250
}
```

**Risk:** Trading history and patterns exposed if system is compromised.

**Remediation:**
```python
import cryptography.fernet

# Encrypt state before saving
def save_state(self):
    key = os.getenv('STATE_ENCRYPTION_KEY')
    if key:
        fernet = Fernet(key.encode())
        encrypted = fernet.encrypt(json.dumps(self.state).encode())
        self.state_file.write_bytes(encrypted)
    else:
        # Warn user
        self.log("WARNING: State file unencrypted!")
```

---

### ✅ GOOD: No Credential Logging

**Finding:** No print/log statements output tokens, keys, or passwords

**Verified:**
```bash
grep -n "print\|log" *.py | grep -i "token\|key\|password"
```
Only generic error messages found, no sensitive data logged.

---

### 🟡 MEDIUM: Python Bytecode (.pyc) Files

**Files:** `__pycache__/*.pyc`
- **Status:** Files exist and are readable
- **Content:** Only variable names, no credential values
- **Risk:** Low, but should be excluded from version control

**Finding:** `.gitignore` correctly excludes `__pycache__/` ✅

---

## 4. Rate Limiting & API Abuse Prevention

### 🟡 MEDIUM: Basic Rate Limiting Only

**Implementation:** Simple `time.sleep()` delays

```python
# trading_bot.py
time.sleep(1)   # Between orders
time.sleep(300) # Between cycles (5 minutes)
time.sleep(60)  # On error
```

**Issues:**
- No exponential backoff on failures
- No rate limit header checking
- No request queuing or throttling
- Could hit Kalshi API limits if many markets are scanned

**Remediation:** Implement proper rate limiting:

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=5,
    backoff_factor=2,  # Exponential backoff
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
self.session.mount("https://", adapter)
```

---

### 🟢 GOOD: Position Size Limits

**Finding:** Risk management parameters in place

```python
MAX_POSITIONS_PER_MARKET=1
MAX_DAILY_TRADES=50
POSITION_SIZE=10  # 10 contracts per trade
```

This limits exposure per trade and per day.

---

## 5. Git Security

### ✅ GOOD: .gitignore Configuration

**Bot directory .gitignore:**
```gitignore
.env
bot_state.json
*.log
*.secret.json
```

**Parent directory .gitignore:**
```gitignore
# Kalshi credentials
kalshi-config.secret.json
*.secret.json
*.secret
```

**Finding:** Credentials properly excluded from version control ✅

---

## 6. Additional Security Concerns

### 🟡 MEDIUM: JWT Token Handling

**Issue:** JWT tokens stored in memory as instance variables

```python
# kalshi_api.py
self.last_token = None
self.token_expires = None
```

**Risk:** If memory is dumped (core dump, debug), tokens could be extracted.

**Mitigation already in place:**
- Tokens expire in 5 minutes ✅
- Refresh on demand ✅

**Recommendation:** Clear tokens immediately after use, don't cache.

---

### 🟢 GOOD: HTTPS Only

**Finding:** All API calls use HTTPS

```python
self.base_url = "https://api.elections.kalshi.com/v1"
```

No plaintext HTTP requests ✅

---

## 7. Security Best Practices Followed

✅ **No hardcoded credentials in code**  
✅ **Credentials gitignored**  
✅ **HTTPS enforced**  
✅ **Position size limits**  
✅ **Daily trade limits**  
✅ **No sensitive data logging**  
✅ **Virtual environment used**  

---

## 8. Critical Vulnerabilities Summary

| Severity | Issue | Risk Level |
|----------|-------|------------|
| 🔴 CRITICAL | NO PAPER TRADING MODE | Immediate financial loss |
| 🔴 CRITICAL | Credentials file 644 permissions | Credential theft |
| 🔴 CRITICAL | No confirmation before trading | Accidental trades |
| 🟡 MEDIUM | Unencrypted state files | Data exposure |
| 🟡 MEDIUM | No .env file usage | Misleading security |
| 🟡 MEDIUM | Basic rate limiting only | API rate limits |

---

## 9. Recommendations for Hardening

### Immediate Actions (Before ANY Use):

1. **Fix credentials file permissions:**
   ```bash
   chmod 600 /Users/tommylu/clawd/kalshi-config.secret.json
   chmod 600 /Users/tommylu/clawd/kalshi-bot/.env
   ```

2. **Add paper trading mode** to `trading_bot.py`:
   - Add `PAPER_TRADING=true` environment variable
   - Check flag before calling `place_order()`
   - Log simulated trades instead of executing

3. **Add confirmation prompt** for live trading:
   - Require explicit `--live` flag
   - Interactive confirmation required
   - Default to dry-run mode

4. **Update .gitignore** to fix *.json overbroad exclusion

---

### Short-term Improvements:

5. **Implement state encryption:**
   - Use `cryptography.fernet` for bot_state.json
   - Generate encryption key from env var or keyring

6. **Improve rate limiting:**
   - Exponential backoff on failures
   - Respect rate limit headers
   - Request queue with throttling

7. **Add audit logging:**
   - Log all trade decisions (separate from debug logs)
   - Include timestamps, market data, rationale
   - Protect logs with same security as state

8. **Either use .env or remove it:**
   - Load credentials from .env using python-dotenv
   - OR document that kalshi-config.secret.json is the only source

---

### Long-term Improvements:

9. **Add unit tests** for trading logic
10. **Implement circuit breaker** for API failures
11. **Add database** for trade history instead of JSON files
12. **Containerize** with Docker for isolation
13. **Add secrets management** (HashiCorp Vault, AWS Secrets Manager)
14. **Implement proper logging framework** (structlog, loguru)
15. **Add monitoring/alerting** for unusual activity

---

## 10. Safe Deployment Checklist

### Pre-Deployment:

- [ ] `chmod 600` on all credential files
- [ ] Set `PAPER_TRADING=true` environment variable
- [ ] Test in simulation mode for 1 week minimum
- [ ] Review and understand all trading logic
- [ ] Set up monitoring for trade execution
- [ ] Configure alerts for errors/unusual activity

### Before Going Live:

- [ ] Backup Kalshi account state
- [ ] Set conservative position sizes (start small)
- [ ] Lower daily trade limits for testing
- [ ] Ensure you have funds to cover losses
- [ ] Write down emergency shutdown procedure
- [ ] Test kill switch (Ctrl+C handling)

### During Operation:

- [ ] Monitor logs for errors
- [ ] Review trades daily
- [ ] Check profit/loss statements
- [ ] Verify no unexpected positions
- [ ] Watch for rate limit warnings

### Emergency Procedures:

**Stop the bot immediately if:**
- Unexpected trades are placed
- Losses exceed daily limit
- API errors persist > 10 minutes
- System behaves abnormally

**Emergency stop:**
```bash
# Kill bot process
pkill -f trading_bot.py

# Cancel all open orders via Kalshi UI
# Review account activity
# Investigate logs before restarting
```

---

## 11. Grading Rubric

| Category | Grade | Notes |
|----------|-------|-------|
| Credential Storage | D | Insecure permissions, misleading .env |
| Code Security | C | No hardcoded secrets, but unsafe defaults |
| Paper Trading | F | No simulation mode at all |
| Data Encryption | D | No encryption for state files |
| Rate Limiting | C | Basic delays only |
| Git Hygiene | B | Proper gitignore, good practices |
| Network Security | B | HTTPS enforced, good token handling |
| Safeguards | F | No confirmation, will trade immediately |

**Overall Grade: D** (Passable for testing, NOT ready for live use)

---

## 12. Conclusion

The Kalshi trading bot is **NOT SAFE FOR LIVE TRADING** in its current state. The absence of paper trading mode and insecure credential storage pose unacceptable risks.

**Required actions before deployment:**
1. Fix file permissions (chmod 600)
2. Implement paper trading mode
3. Add confirmation prompts
4. Test thoroughly in simulation

**Estimated time to secure:** 2-4 hours of development work

---

**Report completed:** 2025-01-30  
**Next review:** After critical issues are addressed  
**Auditor recommendation:** DO NOT DEPLOY until CRITICAL issues are fixed

---

## Appendix: File Permissions Summary

```
Permissions as of 2025-01-30:

/Users/tommylu/clawd/kalshi-config.secret.json  -rw-r--r--  (SHOULD BE -rw-------)
/Users/tommylu/clawd/kalshi-bot/.env              -rw-r--r--  (SHOULD BE -rw-------)
/Users/tommylu/clawd/kalshi-bot/*.py              -rw-r--r--  (acceptable for code)
```

---

*This audit covered the Kalshi trading bot at commit time. Security is an ongoing process - regular audits recommended.*
