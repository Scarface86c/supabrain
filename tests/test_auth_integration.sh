#!/bin/bash
# Integration test for API key authentication
# This script tests the auth middleware in a real scenario

set -e

echo "🔐 Testing API Key Authentication Integration"
echo "=============================================="

# Test 1: Auth disabled (default)
echo ""
echo "Test 1: Auth disabled (default config)"
echo "Expected: Request should succeed without API key"

response=$(curl -s -w "\n%{http_code}" "http://localhost:8080/api/v1/whoami?agent_name=Scar")
status_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$status_code" == "200" ]; then
    echo "✅ PASS: Request succeeded without API key (status: $status_code)"
else
    echo "❌ FAIL: Expected 200, got $status_code"
    echo "Response: $body"
    exit 1
fi

# Test 2: Docs endpoint should always be accessible
echo ""
echo "Test 2: Public endpoints accessible"
echo "Expected: /docs should work without auth"

response=$(curl -s -w "\n%{http_code}" "http://localhost:8080/docs")
status_code=$(echo "$response" | tail -n 1)

if [ "$status_code" == "200" ]; then
    echo "✅ PASS: Public endpoint accessible (status: $status_code)"
else
    echo "❌ FAIL: Expected 200, got $status_code"
    exit 1
fi

# Test 3: Health endpoint
echo ""
echo "Test 3: Health endpoint"
echo "Expected: /health should work without auth"

response=$(curl -s -w "\n%{http_code}" "http://localhost:8080/health")
status_code=$(echo "$response" | tail -n 1)

if [ "$status_code" == "200" ]; then
    echo "✅ PASS: Health check accessible (status: $status_code)"
else
    echo "❌ FAIL: Expected 200, got $status_code"
    exit 1
fi

echo ""
echo "=============================================="
echo "✅ All integration tests passed!"
echo ""
echo "Note: To test with auth enabled:"
echo "1. Generate key: python3 core/auth.py generate"
echo "2. Add to .env: REQUIRE_AUTH=true and API_KEY=<generated_key>"
echo "3. Restart API: bash restart_api.sh"
echo "4. Test: curl -H 'X-API-Key: <key>' http://localhost:8080/api/v1/whoami?agent_name=Scar"
