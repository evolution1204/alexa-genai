#!/usr/bin/env python3
"""
GPT-5 API ローカルテストスクリプト
GPT-5 Responses APIの動作確認用
"""

import requests
import json
import sys

def test_gpt5_api(api_key):
    """GPT-5 APIをテストする"""

    print("=" * 50)
    print("GPT-5 API テスト開始")
    print("=" * 50)

    # GPT-5 Responses API エンドポイント
    url = "https://api.openai.com/v1/responses"

    # ヘッダー
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # テストケース
    test_cases = [
        {
            "name": "基本テスト（日本語）",
            "input": "生成AIとは何ですか？50文字以内で簡潔に答えてください。",
            "model": "gpt-5-mini",
            "reasoning_effort": "low",
            "text_verbosity": "low"
        },
        {
            "name": "最小パラメータテスト",
            "input": "Hello, what is AI?",
            "model": "gpt-5-nano",
            "reasoning_effort": "minimal",
            "text_verbosity": "low"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n--- テスト {i}: {test['name']} ---")

        # リクエストボディ（GPT-5形式）
        data = {
            "model": test["model"],
            "input": test["input"],
            "reasoning": {
                "effort": test["reasoning_effort"]
            },
            "text": {
                "verbosity": test["text_verbosity"]
            }
        }

        print(f"モデル: {test['model']}")
        print(f"入力: {test['input']}")
        print(f"リクエスト: {json.dumps(data, ensure_ascii=False, indent=2)}")

        try:
            # API呼び出し
            print("\nAPIを呼び出しています...")
            response = requests.post(url, headers=headers, json=data, timeout=30)

            print(f"ステータスコード: {response.status_code}")

            # レスポンスの解析
            if response.ok:
                result = response.json()
                print(f"レスポンス: {json.dumps(result, ensure_ascii=False, indent=2)}")

                # output_textの取得
                output_text = result.get('output_text', '')
                if output_text:
                    print(f"\n✅ 成功: {output_text}")
                else:
                    print("⚠️ 警告: output_textが空です")

                # reasoning_textがあれば表示
                if 'reasoning_text' in result:
                    print(f"推論: {result['reasoning_text'][:100]}...")

            else:
                print(f"❌ エラー: {response.status_code}")
                print(f"エラー内容: {response.text}")

                # エラーの詳細を解析
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        print(f"エラータイプ: {error_data['error'].get('type', 'unknown')}")
                        print(f"エラーメッセージ: {error_data['error'].get('message', 'なし')}")
                except:
                    pass

        except requests.exceptions.Timeout:
            print("❌ タイムアウトエラー: 30秒以内に応答がありませんでした")
        except requests.exceptions.ConnectionError:
            print("❌ 接続エラー: APIに接続できませんでした")
        except Exception as e:
            print(f"❌ 予期しないエラー: {str(e)}")

    print("\n" + "=" * 50)
    print("代替案: Chat Completions API (GPT-4)のテスト")
    print("=" * 50)

    # GPT-4での代替テスト
    test_gpt4_api(api_key)

def test_gpt4_api(api_key):
    """比較のためGPT-4 APIもテスト"""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer in 50 words or less."},
            {"role": "user", "content": "What is generative AI?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    print("\nGPT-4 APIテスト...")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.ok:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ GPT-4成功: {content}")
        else:
            print(f"❌ GPT-4エラー: {response.status_code}")
            print(f"詳細: {response.text}")

    except Exception as e:
        print(f"❌ エラー: {str(e)}")

def main():
    print("GPT-5 API ローカルテストツール")
    print("-" * 50)

    # APIキーの入力
    api_key = input("OpenAI APIキーを入力してください (sk-...): ").strip()

    if not api_key:
        print("エラー: APIキーが入力されていません")
        sys.exit(1)

    if not api_key.startswith("sk-"):
        print("警告: APIキーは通常 'sk-' で始まります")

    # テスト実行
    test_gpt5_api(api_key)

    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)
    print("\n解決策:")
    print("1. GPT-5 APIが404の場合 → モデル名を確認 (gpt-5, gpt-5-mini, gpt-5-nano)")
    print("2. 401エラーの場合 → APIキーを確認")
    print("3. 400エラーの場合 → リクエスト形式を確認")
    print("4. GPT-4は動作するがGPT-5が動作しない場合 → GPT-5のアクセス権限を確認")

if __name__ == "__main__":
    main()