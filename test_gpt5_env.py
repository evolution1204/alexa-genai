#!/usr/bin/env python3
"""
GPT-5 API テスト (.envファイルからAPIキー読み込み)
"""

import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# APIキーを環境変数から取得
API_KEY = os.getenv('openai_api_key', '').strip()

def test_gpt5():
    """GPT-5 Responses APIをテスト"""

    print("=" * 60)
    print("GPT-5 API テスト開始")
    print("=" * 60)
    print(f"APIキー: {API_KEY[:10]}...{API_KEY[-4:]}")
    print()

    # GPT-5 Responses API
    url = "https://api.openai.com/v1/responses"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # テスト1: 最小リクエスト
    print("テスト1: 最小リクエスト (gpt-5-mini)")
    print("-" * 40)

    data = {
        "model": "gpt-5-mini",
        "input": "What is generative AI? Answer in one sentence."
    }

    print(f"リクエスト: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"\nステータスコード: {response.status_code}")

        if response.ok:
            result = response.json()
            print(f"レスポンス全体: {json.dumps(result, ensure_ascii=False, indent=2)}")
            output = result.get('output_text', '')
            if output:
                print(f"\n✅ 成功: {output}")
            else:
                print("⚠️ output_textが空です")
        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"エラー内容: {response.text}")

    except Exception as e:
        print(f"❌ 例外発生: {e}")

    # テスト2: パラメータ付きリクエスト
    print("\n" + "=" * 60)
    print("テスト2: パラメータ付きリクエスト (gpt-5-mini)")
    print("-" * 40)

    data = {
        "model": "gpt-5-mini",
        "input": "生成AIとは何ですか？一文で答えてください。",
        "reasoning": {
            "effort": "low"
        },
        "text": {
            "verbosity": "low"
        }
    }

    print(f"リクエスト: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"\nステータスコード: {response.status_code}")

        if response.ok:
            result = response.json()
            print(f"レスポンス: {json.dumps(result, ensure_ascii=False, indent=2)}")
            output = result.get('output_text', '')
            if output:
                print(f"\n✅ 成功: {output}")
            else:
                print("⚠️ output_textが空です")
        else:
            print(f"❌ エラー: {response.text}")

    except Exception as e:
        print(f"❌ 例外発生: {e}")

def test_gpt4_comparison():
    """比較のためGPT-4もテスト"""

    print("\n" + "=" * 60)
    print("比較テスト: GPT-4 Chat Completions API")
    print("-" * 40)

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is generative AI? Answer in one sentence."}
        ],
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"ステータスコード: {response.status_code}")

        if response.ok:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ GPT-4成功: {content}")
        else:
            print(f"❌ GPT-4エラー: {response.text}")

    except Exception as e:
        print(f"❌ 例外発生: {e}")

def test_models_list():
    """利用可能なモデル一覧を取得"""

    print("\n" + "=" * 60)
    print("利用可能なモデル一覧")
    print("-" * 40)

    url = "https://api.openai.com/v1/models"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.ok:
            models = response.json()
            gpt_models = [m['id'] for m in models['data'] if 'gpt' in m['id'].lower()]
            gpt_models.sort()

            print("GPTモデル一覧:")
            for model in gpt_models:
                prefix = "  ✅ " if 'gpt-5' in model else "  - "
                print(f"{prefix}{model}")
        else:
            print(f"❌ エラー: {response.status_code}")

    except Exception as e:
        print(f"❌ 例外発生: {e}")

def main():
    if not API_KEY:
        print("❌ エラー: .envファイルにopenai_api_keyが設定されていません")
        return

    print("OpenAI API テスト")
    print("APIキーを.envから読み込みました")
    print()

    # 利用可能なモデル一覧
    test_models_list()

    # GPT-5テスト
    test_gpt5()

    # GPT-4比較テスト
    test_gpt4_comparison()

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()