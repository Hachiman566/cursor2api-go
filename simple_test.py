#!/usr/bin/env python3
"""Simple test for claude-sonnet-4.6 via cursor2api-go"""

import requests

# Configuration
API_URL = "http://localhost:8002/v1/chat/completions"
API_KEY = "0000"

# Test request
response = requests.post(
    API_URL,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    json={
        "model": "claude-sonnet-4.6",
        "messages": [{"role": "user", "content": "Say hello in one sentence"}],
        "max_tokens": 50
    },
    timeout=60
)

# Print result
if response.status_code == 200:
    result = response.json()
    print("✅ Success!")
    print(f"Response: {result['choices'][0]['message']['content']}")
    print(f"Tokens: {result['usage']['total_tokens']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
