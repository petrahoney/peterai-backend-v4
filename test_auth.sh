#!/bin/bash

API_URL="http://47.254.144.78"
EMAIL="testuser@example.com"
USERNAME="testuser"
PASSWORD="TestPassword123!"
FULLNAME="Test User"

echo "=== PETER AI v4.0 Auth Testing ==="

# 1. Register
echo -e "\n1. Testing REGISTER..."
REGISTER=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d @- <<PAYLOAD
{
  "email": "$EMAIL",
  "username": "$USERNAME",
  "password": "$PASSWORD",
  "full_name": "$FULLNAME"
}
PAYLOAD
)

echo "Register: $REGISTER"

# 2. Login
echo -e "\n2. Testing LOGIN..."
LOGIN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d @- <<PAYLOAD
{
  "email": "$EMAIL",
  "password": "$PASSWORD"
}
PAYLOAD
)

echo "Login: $LOGIN"

# Extract token (jika berhasil)
TOKEN=$(echo $LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ ! -z "$TOKEN" ]; then
  echo "Token extracted: ${TOKEN:0:20}..."
  
  # 3. Get user profile
  echo -e "\n3. Testing GET USER..."
  curl -s -X GET "$API_URL/api/user/me?token=$TOKEN"
fi

echo -e "\n\n=== Tests Complete ==="

