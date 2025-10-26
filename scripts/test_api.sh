#!/bin/bash

# API Test Script
# Tests the Business Search Engine API endpoints

set -e

API_BASE="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Business Search Engine API${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
HEALTH_RESPONSE=$(curl -s "${API_BASE}/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$HEALTH_RESPONSE" | jq . 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Create Search Task
echo -e "${BLUE}Test 2: Create Search Task${NC}"
SEARCH_RESPONSE=$(curl -s -X POST "${API_BASE}/api/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "Google Inc.", "include_website": true}')

echo "$SEARCH_RESPONSE" | jq . 2>/dev/null || echo "$SEARCH_RESPONSE"

TASK_ID=$(echo "$SEARCH_RESPONSE" | jq -r '.task_id' 2>/dev/null)

if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
    echo -e "${GREEN}✓ Search task created with ID: ${TASK_ID}${NC}"
else
    echo -e "${RED}❌ Failed to create search task${NC}"
    exit 1
fi
echo ""

# Test 3: Check Task Status (multiple times)
echo -e "${BLUE}Test 3: Check Task Status${NC}"
echo "Checking status every 5 seconds..."
echo ""

for i in {1..12}; do
    STATUS_RESPONSE=$(curl -s "${API_BASE}/api/status/${TASK_ID}")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status' 2>/dev/null)
    PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress' 2>/dev/null)
    MESSAGE=$(echo "$STATUS_RESPONSE" | jq -r '.message' 2>/dev/null)

    echo -e "${BLUE}Check $i:${NC} Status=${STATUS}, Progress=${PROGRESS}%, Message=${MESSAGE}"

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo -e "${GREEN}✓ Task completed successfully!${NC}"
        echo ""
        echo -e "${GREEN}Results:${NC}"
        echo "$STATUS_RESPONSE" | jq '.result' 2>/dev/null || echo "$STATUS_RESPONSE"
        echo ""
        break
    elif [ "$STATUS" = "failed" ]; then
        echo ""
        echo -e "${RED}❌ Task failed${NC}"
        ERROR=$(echo "$STATUS_RESPONSE" | jq -r '.error' 2>/dev/null)
        echo "Error: $ERROR"
        echo ""
        exit 1
    fi

    if [ $i -lt 12 ]; then
        sleep 5
    fi
done

if [ "$STATUS" != "completed" ]; then
    echo ""
    echo -e "${RED}❌ Task did not complete within 60 seconds${NC}"
    echo "Final status: $STATUS"
    exit 1
fi

# Test 4: Test with Different Companies
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 4: Multiple Company Searches${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

COMPANIES=("Tesla" "Microsoft" "OpenAI")

for COMPANY in "${COMPANIES[@]}"; do
    echo -e "${BLUE}Searching for: ${COMPANY}${NC}"

    RESPONSE=$(curl -s -X POST "${API_BASE}/api/search" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"${COMPANY}\"}")

    TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id' 2>/dev/null)

    if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        echo -e "${GREEN}✓ Task created: ${TASK_ID}${NC}"
    else
        echo -e "${RED}❌ Failed to create task for ${COMPANY}${NC}"
    fi
    echo ""
done

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}API Tests Completed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Check task status at: ${API_BASE}/api/status/{task_id}"
echo "View API docs at: ${API_BASE}/docs"
echo "Monitor tasks at: http://localhost:5555 (Flower)"
echo ""
