#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude API接続テスト
"""
import sys
import os

# 現在のディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

# .envを読み込む
from config import LLM_PROVIDER, CLAUDE_MODEL, ANTHROPIC_API_KEY, warn_if_missing

print("=" * 60)
print("Claude API接続テスト")
print("=" * 60)

# 設定確認
print(f"\nLLM Provider: {LLM_PROVIDER}")
print(f"Claude Model: {CLAUDE_MODEL}")
print(f"API Key: {ANTHROPIC_API_KEY[:20]}...{ANTHROPIC_API_KEY[-10:]}" if ANTHROPIC_API_KEY else "API Key: (not set)")

# 警告チェック
warn_if_missing()

if LLM_PROVIDER != "claude":
    print("\n⚠️  警告: LLM_PROVIDER が 'claude' に設定されていません")
    sys.exit(1)

if not ANTHROPIC_API_KEY:
    print("\n❌ エラー: ANTHROPIC_API_KEY が設定されていません")
    sys.exit(1)

print("\n" + "=" * 60)
print("Claude APIクライアントの初期化...")
print("=" * 60)

try:
    from claude_utils import get_claude_client, call_claude_chat_once

    client = get_claude_client(timeout_sec=10.0)
    print("✅ Claudeクライアントの初期化成功")

    # テストメッセージ
    print("\n" + "=" * 60)
    print("テストメッセージ送信...")
    print("=" * 60)

    test_messages = [
        {"role": "user", "content": "こんにちは！自己紹介してください。50文字以内で簡潔にお願いします。"}
    ]

    system_prompt = "あなたは『ぴこ』。日本語で話す、元気で可愛い相棒アシスタント。一人称は「ぼく」。"

    response = call_claude_chat_once(
        client=client,
        model=CLAUDE_MODEL,
        messages=test_messages,
        timeout_sec=10.0,
        max_tokens=100,
        system_prompt=system_prompt
    )

    if response:
        print("\n✅ Claude APIからの応答:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print(f"\n応答文字数: {len(response)}文字")
        print("\n✅ テスト成功！Claude Sonnet 4.5が正常に動作しています。")
    else:
        print("\n❌ エラー: 応答が空です")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ エラー発生: {type(e).__name__}")
    print(f"詳細: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("すべてのテストが正常に完了しました！")
print("=" * 60)
