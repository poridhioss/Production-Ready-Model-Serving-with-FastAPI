#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base URLs
HTTPS_URL="https://localhost"
API_URL="${HTTPS_URL}/api/v1"

echo "=========================================="
echo "Sentiment Analysis API - Test Script"
echo "=========================================="
echo ""

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Test 1: Health Check
echo "Test 1: Health Check"
response=$(curl -k -s -o /dev/null -w "%{http_code}" ${HTTPS_URL}/health)
if [ "$response" -eq 200 ]; then
    print_result 0 "Health check passed"
else
    print_result 1 "Health check failed (HTTP $response)"
fi
echo ""

# Test 2: Register User
echo "Test 2: User Registration"
TIMESTAMP=$(date +%s)
USERNAME="testuser${TIMESTAMP}"
EMAIL="test${TIMESTAMP}@example.com"
PASSWORD="testpass123"

response=$(curl -k -s -X POST "${API_URL}/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"${USERNAME}\",
        \"email\": \"${EMAIL}\",
        \"password\": \"${PASSWORD}\"
    }")

if echo "$response" | grep -q "\"username\":\"${USERNAME}\""; then
    print_result 0 "User registration successful"
else
    print_result 1 "User registration failed"
fi
echo ""

# Test 3: Login
echo "Test 3: User Login"
response=$(curl -k -s -X POST "${API_URL}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${USERNAME}&password=${PASSWORD}")

TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -n "$TOKEN" ]; then
    print_result 0 "Login successful"
    echo "Token: ${TOKEN:0:20}..."
else
    print_result 1 "Login failed"
fi
echo ""

# Test 4: Sentiment Analysis
echo "Test 4: Single Sentiment Analysis"
response=$(curl -k -s -X POST "${API_URL}/sentiment/analyze" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a great product! I love it!"}')

if echo "$response" | grep -q "\"sentiment\""; then
    print_result 0 "Sentiment analysis successful"
else
    print_result 1 "Sentiment analysis failed"
fi
echo ""

# Test 5: Batch Sentiment Analysis
echo "Test 5: Batch Sentiment Analysis"
response=$(curl -k -s -X POST "${API_URL}/sentiment/analyze/batch" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "texts": [
            "This is amazing!",
            "This is terrible!",
            "I love this product!"
        ]
    }')

if echo "$response" | grep -q "\"task_id\""; then
    TASK_ID=$(echo "$response" | grep -o '"task_id":"[^"]*' | sed 's/"task_id":"//')
    print_result 0 "Batch sentiment analysis started"
    echo "Task ID: $TASK_ID"
else
    print_result 1 "Batch sentiment analysis failed"
fi
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Tests completed. Check results above."
echo ""
echo "To test with Swagger UI, visit:"
echo "  ${HTTPS_URL}/docs"
echo ""