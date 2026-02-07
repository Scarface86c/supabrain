#!/usr/bin/env python3
"""
Test API Key Authentication
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../core'))

from auth import generate_api_key, verify_api_key
from fastapi import HTTPException
import asyncio


class TestAuth(unittest.TestCase):
    """Test authentication functionality"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        # Keys should be non-empty strings
        self.assertIsInstance(key1, str)
        self.assertGreater(len(key1), 20)
        
        # Each generation should be unique
        self.assertNotEqual(key1, key2)
    
    def test_verify_api_key_disabled(self):
        """Test that auth passes when disabled"""
        # Save original env
        original_auth = os.getenv("REQUIRE_AUTH")
        
        # Disable auth
        os.environ["REQUIRE_AUTH"] = "false"
        
        # Reload module to pick up env change
        import importlib
        import auth as auth_module
        importlib.reload(auth_module)
        
        # Should allow any key (or no key)
        result = asyncio.run(auth_module.verify_api_key(None))
        self.assertTrue(result)
        
        result = asyncio.run(auth_module.verify_api_key("any_key"))
        self.assertTrue(result)
        
        # Restore original env
        if original_auth:
            os.environ["REQUIRE_AUTH"] = original_auth
        else:
            os.environ.pop("REQUIRE_AUTH", None)
    
    def test_verify_api_key_missing(self):
        """Test that missing API key is rejected when auth enabled"""
        # Save and set env
        original_auth = os.getenv("REQUIRE_AUTH")
        original_key = os.getenv("API_KEY")
        
        os.environ["REQUIRE_AUTH"] = "true"
        os.environ["API_KEY"] = "test_key_12345"
        
        # Reload module
        import importlib
        import auth as auth_module
        importlib.reload(auth_module)
        
        # Missing key should raise exception
        with self.assertRaises(HTTPException) as context:
            asyncio.run(auth_module.verify_api_key(None))
        
        self.assertEqual(context.exception.status_code, 401)
        
        # Restore env
        if original_auth:
            os.environ["REQUIRE_AUTH"] = original_auth
        else:
            os.environ.pop("REQUIRE_AUTH", None)
        
        if original_key:
            os.environ["API_KEY"] = original_key
        else:
            os.environ.pop("API_KEY", None)
    
    def test_verify_api_key_invalid(self):
        """Test that invalid API key is rejected"""
        # Save and set env
        original_auth = os.getenv("REQUIRE_AUTH")
        original_key = os.getenv("API_KEY")
        
        os.environ["REQUIRE_AUTH"] = "true"
        os.environ["API_KEY"] = "correct_key"
        
        # Reload module
        import importlib
        import auth as auth_module
        importlib.reload(auth_module)
        
        # Wrong key should raise exception
        with self.assertRaises(HTTPException) as context:
            asyncio.run(auth_module.verify_api_key("wrong_key"))
        
        self.assertEqual(context.exception.status_code, 403)
        
        # Restore env
        if original_auth:
            os.environ["REQUIRE_AUTH"] = original_auth
        else:
            os.environ.pop("REQUIRE_AUTH", None)
        
        if original_key:
            os.environ["API_KEY"] = original_key
        else:
            os.environ.pop("API_KEY", None)
    
    def test_verify_api_key_valid(self):
        """Test that valid API key is accepted"""
        # Save and set env
        original_auth = os.getenv("REQUIRE_AUTH")
        original_key = os.getenv("API_KEY")
        
        os.environ["REQUIRE_AUTH"] = "true"
        os.environ["API_KEY"] = "correct_key"
        
        # Reload module
        import importlib
        import auth as auth_module
        importlib.reload(auth_module)
        
        # Correct key should pass
        result = asyncio.run(auth_module.verify_api_key("correct_key"))
        self.assertTrue(result)
        
        # Restore env
        if original_auth:
            os.environ["REQUIRE_AUTH"] = original_auth
        else:
            os.environ.pop("REQUIRE_AUTH", None)
        
        if original_key:
            os.environ["API_KEY"] = original_key
        else:
            os.environ.pop("API_KEY", None)


if __name__ == "__main__":
    unittest.main()
