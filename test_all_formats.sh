#!/bin/bash
# Comprehensive U-tec API Format Test

TOKEN=$(docker exec uteclocal-gateway cat /data/config.json | jq -r '.access_token')
ACCESS=$(docker exec uteclocal-gateway cat /data/config.json | jq -r '.access_key')
SECRET=$(docker exec uteclocal-gateway cat /data/config.json | jq -r '.secret_key')

echo "Testing various U-tec API formats..."
echo "Token: ${TOKEN:0:20}..."
echo ""

# Format 1: Standard with keys in body
echo "=== Format 1: Uhome.Device/GetAll with keys in body ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/action \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"Uhome.Device/GetAll\",\"data\":{},\"accessKey\":\"$ACCESS\",\"secretKey\":\"$SECRET\"}" | head -20
echo ""

# Format 2: Query instead of GetAll
echo "=== Format 2: Uhome.Device/Query ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/action \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"Uhome.Device/Query\",\"data\":{},\"accessKey\":\"$ACCESS\",\"secretKey\":\"$SECRET\"}" | head -20
echo ""

# Format 3: With clientId instead of accessKey
echo "=== Format 3: With clientId ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/action \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"Uhome.Device/GetAll\",\"data\":{},\"clientId\":\"$ACCESS\",\"clientSecret\":\"$SECRET\"}" | head -20
echo ""

# Format 4: Keys at root level, not in each request
echo "=== Format 4: No keys in request at all ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/action \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"Uhome.Device/GetAll\",\"data\":{}}" | head -20
echo ""

# Format 5: Different endpoint
echo "=== Format 5: /device/list endpoint ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/device/list \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}" | head -20
echo ""

# Format 6: GET request instead of POST
echo "=== Format 6: GET request ==="
curl -s -w "Status: %{http_code}\n" "https://api.u-tec.com/action?action=Uhome.Device/GetAll" \
  -H "Authorization: Bearer $TOKEN" | head -20
echo ""

# Format 7: With params wrapper
echo "=== Format 7: With params wrapper ==="
curl -s -w "Status: %{http_code}\n" https://api.u-tec.com/action \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"Uhome.Device/GetAll\",\"params\":{},\"accessKey\":\"$ACCESS\",\"secretKey\":\"$SECRET\"}" | head -20
echo ""

echo "=== Check which format returned Status: 200 ==="
