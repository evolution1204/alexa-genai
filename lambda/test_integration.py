#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合テスト: convo_core.one_shot_answer() でClaude APIが呼ばれるか確認
"""
import sys
import os
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

# 現在のディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("統合テスト: convo_core.one_shot_answer()")
print("=" * 60)

# 設定読み込み
from config import LLM_PROVIDER, CLAUDE_MODEL, ANTHROPIC_API_KEY

print(f"\nLLM Provider: {LLM_PROVIDER}")
print(f"Claude Model: {CLAUDE_MODEL}")
print(f"API Key exists: {bool(ANTHROPIC_API_KEY)}")

if LLM_PROVIDER != "claude":
    print(f"\n⚠️  警告: LLM_PROVIDER が '{LLM_PROVIDER}' に設定されています")
    print("期待値は 'claude' です")

print("\n" + "=" * 60)
print("convo_core.one_shot_answer() を呼び出します...")
print("=" * 60)

try:
    from convo_core import one_shot_answer

    # セッションを準備
    session = {
        "history": []
    }

    # テストクエリ
    test_query = "東京ってどんなところ？30文字以内で教えて。"

    print(f"\nQuery: {test_query}")
    print("\n実行中...\n")

    # one_shot_answer() を呼び出し（ここでLLM分岐が実行される）
    answer = one_shot_answer(session=session, user_query=test_query, snippets=None)

    if answer:
        print("\n" + "=" * 60)
        print("✅ 成功: 応答を取得しました")
        print("=" * 60)
        print(f"\n応答: {answer}")
        print(f"\n文字数: {len(answer)}文字")
        print("\nセッション履歴:")
        print(session)
        print("\n✅ 統合テスト成功！")
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
print("すべての統合テストが完了しました！")
print("=" * 60)
