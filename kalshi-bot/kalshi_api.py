"""
Kalshi API Client
Handles authentication and API requests to Kalshi exchange
"""

import jwt
import time
import requests
import json
import logging
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from parent directory
CONFIG_PATH = Path(__file__).parent.parent / "kalshi-config.secret.json"

# API Configuration
DEFAULT_API_URL = "https://api.elections.kalshi.com/v1"
API_URL_ENV_VAR = "KALSHI_API_URL"

# Token Configuration
TOKEN_EXPIRY_SECONDS = 300  # 5 minutes
TOKEN_BUFFER_SECONDS = 60  # Renew token 60 seconds before expiry

# Request Configuration
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30

class KalshiConfigError(Exception):
    """Raised when configuration is invalid or missing"""
    pass

class KalshiAPIError(Exception):
    """Raised when API request fails after retries"""
    pass

class KalshiClient:
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Kalshi API client with configuration validation

        Args:
            config_path: Optional path to config file. Defaults to CONFIG_PATH

        Raises:
            KalshiConfigError: If configuration is invalid or missing
        """
        config_path = config_path or CONFIG_PATH
        self._validate_config(config_path)

        with open(config_path, 'r') as f:
            config = json.load(f)

        self.api_key_id = config.get('api_key_id')
        self.private_key_str = config.get('private_key', '').strip()

        # Validate required fields
        if not self.api_key_id:
            raise KalshiConfigError("api_key_id is required in config file")
        if not self.private_key_str:
            raise KalshiConfigError("private_key is required in config file")

        # Parse private key
        try:
            self.private_key = serialization.load_pem_private_key(
                self.private_key_str.encode(),
                password=None
            )
        except ValueError as e:
            raise KalshiConfigError(f"Failed to parse private key: {e}")

        # Configure API URL from environment variable or use default
        self.base_url = os.getenv(API_URL_ENV_VAR, DEFAULT_API_URL)
        self.last_token: Optional[str] = None
        self.token_expires: Optional[int] = None
        self.max_retries = MAX_RETRIES

        logger.info(f"KalshiClient initialized successfully (API: {self.base_url})")

    def _validate_config(self, config_path: Path) -> None:
        """
        Validate configuration file exists and is readable

        Args:
            config_path: Path to configuration file

        Raises:
            KalshiConfigError: If config file is missing or unreadable
        """
        if not config_path.exists():
            raise KalshiConfigError(
                f"Configuration file not found: {config_path}\n"
                f"Please create kalshi-config.secret.json with your API credentials"
            )

        if not config_path.is_file():
            raise KalshiConfigError(
                f"Configuration path is not a file: {config_path}"
            )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise KalshiConfigError(
                f"Configuration file is not valid JSON: {e}"
            ) from e
        except PermissionError as e:
            raise KalshiConfigError(
                f"Configuration file is not readable: {config_path}\n"
                f"Please check file permissions"
            ) from e

    def _get_token(self) -> str:
        """
        Generate JWT token for authentication

        Returns:
            JWT token string
        """
        now = int(time.time())

        # Reuse token if still valid (with buffer before expiry)
        if self.last_token and self.token_expires and now < self.token_expires - TOKEN_BUFFER_SECONDS:
            return self.last_token

        # Create JWT payload
        payload = {
            'sub': self.api_key_id,
            'exp': now + TOKEN_EXPIRY_SECONDS,
            'iat': now
        }

        # Sign token
        token = jwt.encode(payload, self.private_key, algorithm='RS256')

        self.last_token = token
        self.token_expires = now + TOKEN_EXPIRY_SECONDS

        return token

    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make authenticated API request with retry logic and exponential backoff

        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint path
            data: Optional request data

        Returns:
            JSON response as dictionary

        Raises:
            KalshiAPIError: If request fails after all retries
        """
        headers = {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{endpoint}"

        last_error = None

        # Retry with exponential backoff: 1s, 2s, 4s
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, params=data, timeout=REQUEST_TIMEOUT_SECONDS)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=REQUEST_TIMEOUT_SECONDS)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Check for HTTP errors
                response.raise_for_status()

                # Validate response is not empty
                if not response.text:
                    logger.warning(f"Empty response from {endpoint}")
                    return {}

                return response.json()

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.ReadTimeout) as e:
                # Network errors - retry with backoff
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        f"Network error on attempt {attempt + 1}/{self.max_retries}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Network error after {self.max_retries} attempts: {e}")

            except requests.exceptions.HTTPError as e:
                # Business logic errors - fail fast
                error_msg = f"HTTP error: {e}"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        error_msg = f"API error: {error_detail}"
                    except:
                        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

                logger.error(error_msg)
                raise KalshiAPIError(error_msg) from e

            except json.JSONDecodeError as e:
                # Invalid JSON response - fail fast
                logger.error(f"Invalid JSON response from {endpoint}: {e}")
                raise KalshiAPIError(f"Invalid JSON response: {e}") from e

            except Exception as e:
                # Other unexpected errors
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        # All retries failed
        raise KalshiAPIError(f"Request failed after {self.max_retries} attempts: {last_error}")

    def get_exchange_status(self) -> Dict[str, Any]:
        """
        Check if exchange is operational

        Returns:
            Exchange status dictionary
        """
        return self._request('GET', '/exchange/status')

    def get_markets(self, limit: int = 100, status: str = 'open') -> Dict[str, Any]:
        """
        List available markets

        Args:
            limit: Maximum number of markets to return
            status: Market status filter ('open', 'closed', etc.)

        Returns:
            Dictionary with 'markets' key containing list of markets

        Note:
            Returns empty dict if API response is invalid
        """
        try:
            params = {
                'limit': limit,
                'status': status
            }
            response = self._request('GET', '/markets', params)

            # Validate response structure
            if not response:
                logger.warning("get_markets: Empty response from API")
                return {'markets': []}

            if 'markets' not in response:
                logger.warning(f"get_markets: Response missing 'markets' key: {list(response.keys())}")
                return {'markets': []}

            if not isinstance(response['markets'], list):
                logger.warning(f"get_markets: 'markets' is not a list: {type(response['markets'])}")
                return {'markets': []}

            return response

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_markets: Unexpected error: {e}")
            return {'markets': []}

    def get_market(self, market_id: str) -> Dict[str, Any]:
        """
        Get specific market details

        Args:
            market_id: Market identifier

        Returns:
            Market details dictionary

        Note:
            Returns empty dict if API response is invalid
        """
        try:
            response = self._request('GET', f'/markets/{market_id}')

            # Validate response
            if not response:
                logger.warning(f"get_market({market_id}): Empty response")
                return {}

            return response

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_market({market_id}): Unexpected error: {e}")
            return {}

    def get_orderbook(self, market_id: str) -> Dict[str, Any]:
        """
        Get order book for a market

        Args:
            market_id: Market identifier

        Returns:
            Orderbook dictionary
        """
        return self._request('GET', f'/markets/{market_id}/orderbook')

    def get_portfolio(self) -> Dict[str, Any]:
        """
        Get current portfolio and positions

        Returns:
            Portfolio dictionary
        """
        try:
            response = self._request('GET', '/portfolio')

            # Validate response
            if not response:
                logger.warning("get_portfolio: Empty response")
                return {'balance': {}}

            return response

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_portfolio: Unexpected error: {e}")
            return {'balance': {}}

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance

        Returns:
            Balance dictionary with 'cash' key

        Note:
            Returns empty dict if API response is invalid
        """
        try:
            portfolio = self.get_portfolio()

            # Validate response structure
            if not portfolio:
                logger.warning("get_balance: Empty portfolio response")
                return {}

            if 'balance' not in portfolio:
                logger.warning(f"get_balance: Response missing 'balance' key")
                return {}

            balance = portfolio['balance']

            if not isinstance(balance, dict):
                logger.warning(f"get_balance: 'balance' is not a dict: {type(balance)}")
                return {}

            return balance

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_balance: Unexpected error: {e}")
            return {}

    def place_order(self, market_id: str, side: str, price: int, count: int, order_type: str = 'limit') -> Dict[str, Any]:
        """
        Place an order

        Args:
            market_id: Market identifier
            side: 'yes' or 'no'
            price: Price in cents (1-99)
            count: Number of contracts
            order_type: 'limit' or 'market'

        Returns:
            Order confirmation dictionary
        """
        # Validate inputs
        if side not in ['yes', 'no']:
            raise ValueError(f"Invalid side: {side}. Must be 'yes' or 'no'")

        if not 1 <= price <= 99:
            raise ValueError(f"Invalid price: {price}. Must be between 1 and 99 cents")

        if count <= 0:
            raise ValueError(f"Invalid count: {count}. Must be positive")

        if order_type not in ['limit', 'market']:
            raise ValueError(f"Invalid order_type: {order_type}. Must be 'limit' or 'market'")

        order = {
            'market_id': market_id,
            'side': side,
            'price': price,
            'count': count,
            'type': order_type
        }

        return self._request('POST', '/orders', order)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order

        Args:
            order_id: Order identifier

        Returns:
            Cancellation confirmation dictionary
        """
        return self._request('POST', f'/orders/{order_id}/cancel')

    def get_open_orders(self) -> Dict[str, Any]:
        """
        Get all open orders

        Returns:
            Dictionary with orders list
        """
        try:
            response = self._request('GET', '/orders', {'status': 'open'})

            if not response:
                return {'orders': []}

            return response

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_open_orders: Unexpected error: {e}")
            return {'orders': []}

    def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions

        Returns:
            Positions dictionary
        """
        try:
            response = self._request('GET', '/portfolio/positions')

            if not response:
                return {'positions': []}

            return response

        except KalshiAPIError:
            raise
        except Exception as e:
            logger.error(f"get_positions: Unexpected error: {e}")
            return {'positions': []}


if __name__ == "__main__":
    # Test connection
    client: KalshiClient = KalshiClient()

    print("Testing Kalshi API connection...")

    try:
        # Check exchange status
        status: Dict[str, Any] = client.get_exchange_status()
        print(f"✓ Exchange Status: {status.get('status', 'unknown')}")

        # Get balance
        balance: Dict[str, Any] = client.get_balance()
        print(f"✓ Balance: ${balance.get('cash', 0)}")

        # Get open markets
        markets: Dict[str, Any] = client.get_markets(limit=10)
        print(f"✓ Found {len(markets.get('markets', []))} markets")

        print("\nAPI connection successful!")

    except KalshiConfigError as e:
        print(f"✗ Configuration Error: {e}")
    except KalshiAPIError as e:
        print(f"✗ API Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API credentials in kalshi-config.secret.json")
        print("2. Verify your account has API access enabled")
        print("3. Check https://docs.kalshi.com for API status")
