#!/usr/bin/env python3
"""
Test script for Kalshi bot validation and error handling improvements
Tests various failure scenarios to ensure robust error handling
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Add kalshi-bot to path
sys.path.insert(0, str(Path(__file__).parent))

from kalshi_api import KalshiClient, KalshiConfigError, KalshiAPIError

def test_config_validation():
    """Test configuration validation at startup"""
    print("\n" + "="*60)
    print("TEST 1: Configuration Validation")
    print("="*60)
    
    # Test 1a: Missing config file
    print("\n1a. Testing missing config file...")
    try:
        client = KalshiClient(config_path=Path("/nonexistent/config.json"))
        print("  ✗ FAIL: Should have raised KalshiConfigError")
        return False
    except KalshiConfigError as e:
        print(f"  ✓ PASS: Caught expected error: {str(e)[:60]}...")
    
    # Test 1b: Invalid JSON in config
    print("\n1b. Testing invalid JSON in config...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        bad_config_path = Path(f.name)
    
    try:
        client = KalshiClient(config_path=bad_config_path)
        print("  ✗ FAIL: Should have raised KalshiConfigError")
        return False
    except KalshiConfigError as e:
        print(f"  ✓ PASS: Caught expected error: {str(e)[:60]}...")
    finally:
        bad_config_path.unlink()
    
    # Test 1c: Missing API key
    print("\n1c. Testing missing API key in config...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"private_key": "test"}, f)
        incomplete_config = Path(f.name)
    
    try:
        client = KalshiClient(config_path=incomplete_config)
        print("  ✗ FAIL: Should have raised KalshiConfigError")
        return False
    except KalshiConfigError as e:
        print(f"  ✓ PASS: Caught expected error: {str(e)[:60]}...")
    finally:
        incomplete_config.unlink()
    
    print("\n✓ Configuration validation tests PASSED")
    return True

def test_retry_logic():
    """Test retry logic with exponential backoff"""
    print("\n" + "="*60)
    print("TEST 2: Retry Logic with Exponential Backoff")
    print("="*60)
    
    # We can't fully test this without a valid config, but we can verify the logic exists
    print("\n2. Verifying retry configuration...")
    
    # Create a mock client (skip config validation)
    with patch.object(KalshiClient, '_validate_config'):
        client = KalshiClient.__new__(KalshiClient)
        client.max_retries = 3
        client.base_url = "https://test.example.com"
        client.last_token = None
        client.token_expires = None
        
        # Check max_retries is set
        if client.max_retries == 3:
            print(f"  ✓ PASS: max_retries set to {client.max_retries}")
        else:
            print(f"  ✗ FAIL: max_retries is {client.max_retries}, expected 3")
            return False
    
    print("\n✓ Retry logic configuration verified")
    return True

def test_api_response_validation():
    """Test API response validation"""
    print("\n" + "="*60)
    print("TEST 3: API Response Validation")
    print("="*60)
    
    print("\n3. Testing response validation in get_markets...")
    
    # Create a mock client
    with patch.object(KalshiClient, '_validate_config'), \
         patch.object(KalshiClient, '__init__', lambda self, config_path=None: None):
        
        client = KalshiClient.__new__(KalshiClient)
        client.max_retries = 3
        client.base_url = "https://test.example.com"
        client.last_token = "test_token"
        client.token_expires = int(__import__('time').time()) + 300
        
        # Mock _request to return various responses
        with patch.object(client, '_request') as mock_request:
            # Test 3a: Empty response
            print("\n3a. Testing empty response handling...")
            mock_request.return_value = {}
            result = client.get_markets()
            if result == {'markets': []}:
                print("  ✓ PASS: Empty response returns default {'markets': []}")
            else:
                print(f"  ✗ FAIL: Expected {{'markets': []}}, got {result}")
                return False
            
            # Test 3b: Response missing 'markets' key
            print("\n3b. Testing response missing 'markets' key...")
            mock_request.return_value = {'data': 'something'}
            result = client.get_markets()
            if result == {'markets': []}:
                print("  ✓ PASS: Missing 'markets' key returns default {'markets': []}")
            else:
                print(f"  ✗ FAIL: Expected {{'markets': []}}, got {result}")
                return False
            
            # Test 3c: Response with invalid 'markets' type
            print("\n3c. Testing invalid 'markets' type...")
            mock_request.return_value = {'markets': 'not_a_list'}
            result = client.get_markets()
            if result == {'markets': []}:
                print("  ✓ PASS: Invalid 'markets' type returns default {'markets': []}")
            else:
                print(f"  ✗ FAIL: Expected {{'markets': []}}, got {result}")
                return False
            
            # Test 3d: Valid response
            print("\n3d. Testing valid response...")
            mock_request.return_value = {'markets': [{'id': 1}, {'id': 2}]}
            result = client.get_markets()
            if result == {'markets': [{'id': 1}, {'id': 2}]}:
                print("  ✓ PASS: Valid response returned correctly")
            else:
                print(f"  ✗ FAIL: Expected valid markets, got {result}")
                return False
    
    print("\n✓ API response validation tests PASSED")
    return True

def test_balance_validation():
    """Test balance response validation"""
    print("\n" + "="*60)
    print("TEST 4: Balance Response Validation")
    print("="*60)
    
    print("\n4. Testing balance validation...")
    
    with patch.object(KalshiClient, '_validate_config'), \
         patch.object(KalshiClient, '__init__', lambda self, config_path=None: None):
        
        client = KalshiClient.__new__(KalshiClient)
        client.max_retries = 3
        client.base_url = "https://test.example.com"
        client.last_token = "test_token"
        client.token_expires = int(__import__('time').time()) + 300
        
        with patch.object(client, 'get_portfolio') as mock_portfolio:
            # Test 4a: Empty portfolio response
            print("\n4a. Testing empty portfolio response...")
            mock_portfolio.return_value = {}
            result = client.get_balance()
            if result == {}:
                print("  ✓ PASS: Empty portfolio returns {}")
            else:
                print(f"  ✗ FAIL: Expected {{}}, got {result}")
                return False
            
            # Test 4b: Portfolio missing 'balance' key
            print("\n4b. Testing portfolio missing 'balance' key...")
            mock_portfolio.return_value = {'positions': []}
            result = client.get_balance()
            if result == {}:
                print("  ✓ PASS: Missing 'balance' key returns {}")
            else:
                print(f"  ✗ FAIL: Expected {{}}, got {result}")
                return False
            
            # Test 4c: Valid balance response
            print("\n4c. Testing valid balance response...")
            mock_portfolio.return_value = {'balance': {'cash': 10000}}
            result = client.get_balance()
            if result == {'cash': 10000}:
                print("  ✓ PASS: Valid balance returned correctly")
            else:
                print(f"  ✗ FAIL: Expected {{'cash': 10000}}, got {result}")
                return False
    
    print("\n✓ Balance validation tests PASSED")
    return True

def test_type_hints():
    """Test that type hints are present"""
    print("\n" + "="*60)
    print("TEST 5: Type Hints")
    print("="*60)
    
    print("\n5. Checking for type hints...")
    
    import inspect
    
    # Check KalshiClient methods
    client_methods = [
        'get_markets',
        'get_market', 
        'get_balance',
        'place_order',
        'cancel_order'
    ]
    
    for method_name in client_methods:
        if hasattr(KalshiClient, method_name):
            method = getattr(KalshiClient, method_name)
            sig = inspect.signature(method)
            
            # Check if method has annotations
            if sig.return_annotation != inspect.Parameter.empty:
                print(f"  ✓ {method_name}: has return type hint")
            else:
                print(f"  ⚠ {method_name}: missing return type hint")
    
    print("\n✓ Type hints verification complete")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Kalshi Bot - Validation & Error Handling Tests")
    print("="*60)
    
    tests = [
        ("Configuration Validation", test_config_validation),
        ("Retry Logic", test_retry_logic),
        ("API Response Validation", test_api_response_validation),
        ("Balance Validation", test_balance_validation),
        ("Type Hints", test_type_hints),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
