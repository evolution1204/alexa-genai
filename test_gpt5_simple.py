#!/usr/bin/env python3
"""
GPT-5 API 最小テスト
最もシンプルな形でGPT-5 APIをテスト
"""

import requests
import json

# APIキーをここに設定
API_KEY = ""  # "sk-..." の形式でAPIキーを入力

def test_gpt5():
    """GPT-5の最小テスト"""

    # GPT-5 Responses API
    url = "https://api.openai.com/v1/responses"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 最小のリクエスト
    data = {
        "model": "gpt-5-mini",
        "input": "What is AI? Answer in one sentence."
    }

    print("Testing GPT-5 API...")
    print(f"Request: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.ok:
            result = response.json()
            output = result.get('output_text', 'No output_text in response')
            print(f"\n✅ Success: {output}")
        else:
            print(f"\n❌ Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception: {e}")

def test_gpt4():
    """比較用: GPT-4のテスト"""

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is AI? Answer in one sentence."}
        ],
        "max_tokens": 50
    }

    print("\n" + "="*50)
    print("Testing GPT-4 API for comparison...")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")

        if response.ok:
            result = response.json()
            output = result['choices'][0]['message']['content']
            print(f"✅ GPT-4 works: {output}")
        else:
            print(f"❌ GPT-4 error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ エラー: API_KEYを設定してください")
        print("このファイルを編集して、11行目にAPIキーを設定してください")
        print('例: API_KEY = "sk-proj-..."')
    else:
        print("GPT-5 API Test")
        print("=" * 50)
        test_gpt5()
        test_gpt4()
        print("\n" + "=" * 50)
        print("Test completed")