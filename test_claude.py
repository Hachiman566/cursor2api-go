#!/usr/bin/env python3
"""Test script for Claude Sonnet 4.6 model via cursor2api-go"""

import requests
import json

# API configuration
API_BASE = "http://localhost:8002"
API_KEY = "0000"
MODEL = "claude-sonnet-4.6"

def test_chat_completion():
    """Test non-streaming chat completion"""
    print("Testing chat completion...")

    url = f"{API_BASE}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Hello! Please say hello back in one sentence."}
        ],
        "max_tokens": 100,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"\n✅ Chat completion successful!")
        print(f"Model: {result.get('model')}")
        print(f"Response: {result['choices'][0]['message']['content']}")
        print(f"Usage: {result.get('usage')}")

        return True
    except Exception as e:
        print(f"\n❌ Chat completion failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def test_streaming_chat():
    """Test streaming chat completion"""
    print("\n\nTesting streaming chat completion...")

    url = f"{API_BASE}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Count from 1 to 5"}
        ],
        "max_tokens": 100,
        "stream": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        response.raise_for_status()

        print(f"\n✅ Streaming response:")
        full_content = ""

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                full_content += content
                    except json.JSONDecodeError:
                        pass

        print(f"\n\nFull response: {full_content}")
        return True
    except Exception as e:
        print(f"\n❌ Streaming failed: {e}")
        return False

def test_anthropic_format():
    """Test Anthropic format API"""
    print("\n\nTesting Anthropic format API...")

    url = f"{API_BASE}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    }

    payload = {
        "model": MODEL,
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "What is 2+2? Answer in one sentence."}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"\n✅ Anthropic format successful!")
        print(f"Response: {result['content'][0]['text']}")
        print(f"Usage: {result.get('usage')}")

        return True
    except Exception as e:
        print(f"\n❌ Anthropic format failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def test_models_list():
    """Test models list endpoint"""
    print("\n\nTesting models list...")

    url = f"{API_BASE}/v1/models"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        result = response.json()

        print(f"\n✅ Models list retrieved!")
        print(f"Available models:")
        for model in result['data']:
            print(f"  - {model['id']}")

        # Check if our model is in the list
        model_ids = [m['id'] for m in result['data']]
        if MODEL in model_ids:
            print(f"\n✅ Model '{MODEL}' is available!")
            return True
        else:
            print(f"\n⚠️  Model '{MODEL}' not found in available models")
            return False
    except Exception as e:
        print(f"\n❌ Models list failed: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n\nTesting health endpoint...")

    url = f"{API_BASE}/health"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        result = response.json()
        print(f"\n✅ Service is healthy!")
        print(f"Status: {result}")
        return True
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print(f"Testing cursor2api-go with model: {MODEL}")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Health Check", test_health()))
    results.append(("Models List", test_models_list()))
    results.append(("Chat Completion", test_chat_completion()))
    results.append(("Streaming Chat", test_streaming_chat()))
    results.append(("Anthropic Format", test_anthropic_format()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        exit(1)
