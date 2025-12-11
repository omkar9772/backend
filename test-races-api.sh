#!/bin/bash

# Get auth token first (using test credentials)
echo "Testing races API..."
echo ""

# Test the list races endpoint
echo "GET /api/v1/admin/races?skip=0&limit=15"
curl -X GET 'http://localhost:8000/api/v1/admin/races?skip=0&limit=15' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer test-token' \
  2>/dev/null | python3 -m json.tool | head -30

echo ""
echo "If you see authentication error above, you need to login first in the UI and then test"
