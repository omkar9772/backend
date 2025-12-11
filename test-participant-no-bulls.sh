#!/bin/bash

# Test script to verify adding participants without bulls

echo "=== Testing Add Participant Without Bulls ==="

# Step 1: Get admin token
echo -e "\n1. Getting admin token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get admin token"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo "✅ Got admin token: ${TOKEN:0:20}..."

# Step 2: Get first race ID
echo -e "\n2. Getting race ID..."
RACES_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/admin/races \
  -H "Authorization: Bearer $TOKEN")

RACE_ID=$(echo $RACES_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$RACE_ID" ]; then
  echo "❌ No races found"
  exit 1
fi

echo "✅ Found race: $RACE_ID"

# Step 3: Get owner IDs
echo -e "\n3. Getting owner IDs..."
OWNERS_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/admin/owners \
  -H "Authorization: Bearer $TOKEN")

OWNER1_ID=$(echo $OWNERS_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
OWNER2_ID=$(echo $OWNERS_RESPONSE | grep -o '"id":"[^"]*' | head -2 | tail -1 | cut -d'"' -f4)

if [ -z "$OWNER1_ID" ] || [ -z "$OWNER2_ID" ]; then
  echo "❌ Need at least 2 owners"
  exit 1
fi

echo "✅ Found owners: $OWNER1_ID and $OWNER2_ID"

# Step 4: Add participant without bulls
echo -e "\n4. Adding participant without bulls..."
RESULT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/admin/race-results \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"race_id\": \"$RACE_ID\",
    \"owner1_id\": \"$OWNER1_ID\",
    \"owner2_id\": \"$OWNER2_ID\",
    \"position\": 1,
    \"time_milliseconds\": 45000,
    \"is_disqualified\": false
  }")

echo "Response: $RESULT_RESPONSE"

if echo "$RESULT_RESPONSE" | grep -q "Participant added successfully"; then
  echo "✅ Successfully added participant without bulls!"
else
  echo "❌ Failed to add participant"
  exit 1
fi

echo -e "\n=== Test Complete ==="
