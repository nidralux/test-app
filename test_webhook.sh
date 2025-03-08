#!/bin/bash
# Script to test the Jira webhook functionality

# Define local server URL (adjust if needed)
SERVER_URL="http://localhost:5000"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Jira webhook functionality...${NC}"

# Test 1: Basic connectivity test
echo -e "\n${YELLOW}Test 1: Basic connectivity check...${NC}"
curl -s "$SERVER_URL/webhook-test" | grep -q "success" && \
    echo -e "${GREEN}✓ Basic connectivity test passed${NC}" || \
    echo -e "${RED}✗ Basic connectivity test failed${NC}"

# Test 2: Send a mock webhook payload for a Ready for QA transition
echo -e "\n${YELLOW}Test 2: Sending mock Ready for QA webhook...${NC}"
RESPONSE=$(curl -s -X POST "$SERVER_URL/jira-webhook" \
    -H "Content-Type: application/json" \
    -d '{
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "TEST-123",
            "fields": {
                "summary": "Test ticket for webhook",
                "description": "This is a test ticket to verify webhook functionality",
                "status": {
                    "name": "Ready for QA"
                }
            }
        },
        "changelog": {
            "items": [
                {
                    "field": "status",
                    "fromString": "In Progress",
                    "toString": "Ready for QA"
                }
            ]
        }
    }')

echo "Response: $RESPONSE"
echo -e "${GREEN}✓ Mock webhook test completed${NC}"

# Test 3: Use the test endpoint for a specific ticket
echo -e "\n${YELLOW}Test 3: Using direct test endpoint...${NC}"
read -p "Enter a Jira ticket key to test (e.g., PROJECT-123) or press Enter to skip: " TICKET_KEY

if [ -n "$TICKET_KEY" ]; then
    echo "Testing with ticket: $TICKET_KEY"
    curl -s "$SERVER_URL/test-qa-transition/$TICKET_KEY"
    echo -e "\n${GREEN}✓ Direct test completed${NC}"
else
    echo -e "${YELLOW}Test skipped${NC}"
fi

echo -e "\n${YELLOW}All tests completed. Check the application logs for details.${NC}" 