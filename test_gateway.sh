#!/bin/bash
# Test script for U-tec Gateway Auto-Refresh functionality
# This script runs a series of tests to verify the enhanced gateway is working correctly

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
DEVICE_ID="${DEVICE_ID:-}"  # Optional: set to test lock/unlock

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}  ✓ PASS${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_fail() {
    echo -e "${RED}  ✗ FAIL${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_info() {
    echo -e "${YELLOW}  ℹ INFO${NC} $1"
}

echo "================================================"
echo "U-tec Gateway Auto-Refresh Test Suite"
echo "================================================"
echo ""
echo "Testing gateway at: $GATEWAY_URL"
echo ""

# Test 1: Health Check
print_test "Test 1: Health Check Endpoint"
if HEALTH=$(curl -s -f "$GATEWAY_URL/health"); then
    print_pass "Health endpoint accessible"
    
    # Check if response contains expected fields
    if echo "$HEALTH" | jq -e '.status' > /dev/null 2>&1; then
        print_pass "Health response has 'status' field"
    else
        print_fail "Health response missing 'status' field"
    fi
    
    if echo "$HEALTH" | jq -e '.token_valid' > /dev/null 2>&1; then
        TOKEN_VALID=$(echo "$HEALTH" | jq -r '.token_valid')
        if [ "$TOKEN_VALID" = "true" ]; then
            print_pass "Token is valid"
        else
            print_fail "Token is not valid"
        fi
    else
        print_fail "Health response missing 'token_valid' field"
    fi
    
    if echo "$HEALTH" | jq -e '.auto_refresh_enabled' > /dev/null 2>&1; then
        AUTO_REFRESH=$(echo "$HEALTH" | jq -r '.auto_refresh_enabled')
        if [ "$AUTO_REFRESH" = "true" ]; then
            print_pass "Auto-refresh is enabled"
        else
            print_fail "Auto-refresh is disabled"
        fi
    else
        print_fail "Health response missing 'auto_refresh_enabled' field"
    fi
else
    print_fail "Health endpoint not accessible"
fi
echo ""

# Test 2: Configuration Endpoint
print_test "Test 2: Configuration Endpoint"
if CONFIG=$(curl -s -f "$GATEWAY_URL/api/config"); then
    print_pass "Config endpoint accessible"
    
    # Check for token status object
    if echo "$CONFIG" | jq -e '.token_status' > /dev/null 2>&1; then
        print_pass "Config has token_status object"
        
        HAS_TOKEN=$(echo "$CONFIG" | jq -r '.token_status.has_token')
        HAS_REFRESH=$(echo "$CONFIG" | jq -r '.token_status.has_refresh_token')
        IS_EXPIRED=$(echo "$CONFIG" | jq -r '.token_status.is_expired')
        EXPIRES_AT=$(echo "$CONFIG" | jq -r '.token_status.expires_at')
        
        print_info "Has access token: $HAS_TOKEN"
        print_info "Has refresh token: $HAS_REFRESH"
        print_info "Is expired: $IS_EXPIRED"
        print_info "Expires at: $EXPIRES_AT"
        
        if [ "$HAS_TOKEN" = "true" ] && [ "$HAS_REFRESH" = "true" ]; then
            print_pass "Both tokens present"
        else
            print_fail "Missing tokens (may need OAuth setup)"
        fi
        
        if [ "$IS_EXPIRED" = "false" ]; then
            print_pass "Token not expired"
        else
            print_fail "Token is expired"
        fi
    else
        print_fail "Config missing token_status object"
    fi
    
    # Check for auto-refresh settings
    AUTO_REFRESH=$(echo "$CONFIG" | jq -r '.auto_refresh_enabled')
    BUFFER_MIN=$(echo "$CONFIG" | jq -r '.refresh_buffer_minutes')
    
    print_info "Auto-refresh enabled: $AUTO_REFRESH"
    print_info "Refresh buffer minutes: $BUFFER_MIN"
else
    print_fail "Config endpoint not accessible"
fi
echo ""

# Test 3: Manual Refresh Endpoint
print_test "Test 3: Manual Token Refresh"
if REFRESH_RESPONSE=$(curl -s -f -X POST "$GATEWAY_URL/api/oauth/refresh"); then
    if echo "$REFRESH_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        STATUS=$(echo "$REFRESH_RESPONSE" | jq -r '.status')
        if [ "$STATUS" = "ok" ]; then
            print_pass "Manual refresh endpoint works"
            MESSAGE=$(echo "$REFRESH_RESPONSE" | jq -r '.message')
            print_info "$MESSAGE"
        else
            print_fail "Manual refresh returned error status"
        fi
    else
        print_fail "Manual refresh response invalid"
    fi
else
    print_info "Manual refresh failed (may need valid refresh token)"
fi
echo ""

# Test 4: Devices Endpoint
print_test "Test 4: Devices Discovery"
if DEVICES=$(curl -s -f "$GATEWAY_URL/api/devices"); then
    print_pass "Devices endpoint accessible"
    
    if echo "$DEVICES" | jq -e '.payload.devices' > /dev/null 2>&1; then
        DEVICE_COUNT=$(echo "$DEVICES" | jq -r '.payload.devices | length')
        print_pass "Found $DEVICE_COUNT device(s)"
        
        if [ "$DEVICE_COUNT" -gt 0 ]; then
            echo "$DEVICES" | jq -r '.payload.devices[] | "  - \(.name // "Unknown") (\(.id))"' | head -5
        fi
    else
        print_info "No devices found or invalid response format"
    fi
else
    print_info "Devices endpoint failed (may need valid token)"
fi
echo ""

# Test 5: Status Query (if device ID provided)
if [ -n "$DEVICE_ID" ]; then
    print_test "Test 5: Device Status Query"
    if STATUS=$(curl -s -f -X POST "$GATEWAY_URL/api/status" \
        -H "Content-Type: application/json" \
        -d "{\"id\":\"$DEVICE_ID\"}"); then
        print_pass "Status query successful for device $DEVICE_ID"
        echo "$STATUS" | jq '.' | head -20
    else
        print_fail "Status query failed for device $DEVICE_ID"
    fi
    echo ""
else
    print_info "Skipping Test 5: Device status query (set DEVICE_ID to enable)"
    echo ""
fi

# Test 6: Latest Status Endpoint
print_test "Test 6: Latest Status Cache"
if LATEST=$(curl -s -f "$GATEWAY_URL/api/status/latest"); then
    print_pass "Latest status endpoint accessible"
    
    LAST_UPDATED=$(echo "$LATEST" | jq -r '.last_updated')
    if [ "$LAST_UPDATED" != "0" ] && [ "$LAST_UPDATED" != "null" ]; then
        TIMESTAMP=$(date -d "@$LAST_UPDATED" 2>/dev/null || date -r "$LAST_UPDATED" 2>/dev/null || echo "Unknown")
        print_pass "Status cache last updated: $TIMESTAMP"
    else
        print_info "Status cache not yet populated"
    fi
else
    print_fail "Latest status endpoint not accessible"
fi
echo ""

# Test 7: Logs Endpoint
print_test "Test 7: Logs Endpoint"
if LOGS=$(curl -s -f "$GATEWAY_URL/logs"); then
    print_pass "Logs endpoint accessible"
    
    LOG_LINES=$(echo "$LOGS" | wc -l)
    print_info "Log has $LOG_LINES lines"
    
    # Check for important log messages
    if echo "$LOGS" | grep -q "Gateway started"; then
        print_pass "Found startup log message"
    fi
    
    if echo "$LOGS" | grep -q "Token refresh"; then
        print_pass "Found token refresh log messages"
    fi
    
    if echo "$LOGS" | grep -q "ERROR"; then
        ERROR_COUNT=$(echo "$LOGS" | grep -c "ERROR")
        print_info "Found $ERROR_COUNT error messages in logs"
    fi
else
    print_fail "Logs endpoint not accessible"
fi
echo ""

# Test 8: Docker Container Check
print_test "Test 8: Docker Container Status"
if command -v docker &> /dev/null; then
    if docker ps | grep -q "uteclocal"; then
        print_pass "Gateway container is running"
        
        CONTAINER_NAME=$(docker ps --filter "name=uteclocal" --format "{{.Names}}" | head -1)
        if [ -n "$CONTAINER_NAME" ]; then
            print_info "Container name: $CONTAINER_NAME"
            
            # Check if APScheduler is installed
            if docker exec "$CONTAINER_NAME" pip list 2>/dev/null | grep -q "APScheduler"; then
                print_pass "APScheduler is installed in container"
            else
                print_fail "APScheduler not found in container"
            fi
        fi
    else
        print_fail "Gateway container not running"
    fi
else
    print_info "Docker not available for container checks"
fi
echo ""

# Test 9: Token Refresh Schedule Check
print_test "Test 9: Token Refresh Schedule"
if [ -n "$CONTAINER_NAME" ]; then
    RECENT_LOGS=$(docker logs "$CONTAINER_NAME" --tail 500 2>&1)
    
    if echo "$RECENT_LOGS" | grep -q "token_refresh"; then
        print_pass "Token refresh scheduler job found in logs"
    else
        print_info "Token refresh scheduler job not yet logged"
    fi
    
    if echo "$RECENT_LOGS" | grep -q "status_poll"; then
        print_pass "Status poll scheduler job found in logs"
    else
        print_info "Status poll scheduler job not yet logged"
    fi
    
    if echo "$RECENT_LOGS" | grep -q "Scheduled token refresh"; then
        print_pass "Found scheduled token refresh execution"
    else
        print_info "No scheduled token refresh execution yet (check back in 5 minutes)"
    fi
else
    print_info "Skipping scheduler checks (container not identified)"
fi
echo ""

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Your gateway appears to be configured correctly for automatic token refresh."
    echo "Monitor the logs over the next few hours to ensure scheduled refreshes work:"
    echo "  docker compose -p uteclocal logs -f gateway | grep refresh"
    EXIT_CODE=0
else
    echo -e "${YELLOW}⚠️  Some tests failed or were skipped${NC}"
    echo ""
    echo "Common issues:"
    echo "  1. OAuth not yet configured - complete OAuth flow in web UI"
    echo "  2. No devices found - ensure your U-tec account has locks"
    echo "  3. Token expired - manually refresh via web UI or API"
    echo ""
    echo "Check the implementation guide for troubleshooting:"
    echo "  cat IMPLEMENTATION_GUIDE.md"
    EXIT_CODE=1
fi

echo ""
echo "================================================"
exit $EXIT_CODE
