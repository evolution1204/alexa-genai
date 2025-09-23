# Alexa GenAI Assistant - 教訓と学び

## 📝 プロジェクト概要
- **プロジェクト名**: Alexa GenAI Assistant
- **期間**: 2025年9月
- **主な技術**: Alexa Skills Kit, AWS Lambda, OpenAI API (GPT-5)

## 🎓 重要な教訓

### 1. APIモデルの確認を怠らない

#### 問題
- GPT-5が存在しないという誤った認識を繰り返した
- 実際にはGPT-5は2024年にリリースされていた（2024年9月30日ナレッジカットオフ）

#### 教訓
- **ユーザーの指摘は真摯に受け止める**
- **思い込みではなく、必ず最新情報を確認する**
- **APIドキュメントは定期的に更新されるため、常に最新版を参照**

#### 対策
```python
# 利用可能なモデル（2025年9月時点）
models = [
    "gpt-5",        # フルサイズ（$1.25/$10 per 1M tokens）
    "gpt-5-mini",   # 中サイズ（$0.25/$5 per 1M tokens）
    "gpt-5-nano",   # 小サイズ（$0.05/$2.50 per 1M tokens）
    "gpt-4o",       # マルチモーダル対応
    "gpt-4o-mini",  # 高効率版
]
```

### 2. GPT-5 API統合の正確性

#### GPT-5の2つのAPIエンドポイント

##### 1. Responses API（新しい、推奨）
```python
# GPT-5専用の新しいResponses API
url = "https://api.openai.com/v1/responses"

# リクエスト形式
data = {
    "model": "gpt-5-mini",
    "input": "ユーザーの質問",
    "reasoning": {"effort": "medium"},  # low, medium, high
    "text": {"verbosity": "medium"}     # low, medium, high
}

# レスポンス解析
response['output_text']  # 直接テキストを取得
```

##### 2. Chat Completions API（従来互換）
```python
# 従来のChat Completions API（GPT-5でも利用可）
url = "https://api.openai.com/v1/chat/completions"

# リクエスト形式
data = {
    "model": "gpt-5-mini",
    "messages": [
        {"role": "system", "content": "システムプロンプト"},
        {"role": "user", "content": "ユーザー入力"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
}

# レスポンス解析
response['choices'][0]['message']['content']
```

#### GPT-5の新機能
- **reasoning effort**: 推論の深さを制御（minimal, low, medium, high）
- **verbosity**: 出力の詳細度を制御（low, medium, high）
- **custom tools**: プレーンテキストでのツール呼び出し
- **allowed tools**: 利用可能なツールの制限

### 3. Alexaスキルの制約事項

#### タイムアウト制限
- **Alexaの制限**: 8秒以内に応答必須
- **対策**: API呼び出しのタイムアウトを7秒に設定

```python
response = requests.post(url, headers=headers, json=data, timeout=7)
```

#### セッション管理
- **会話履歴の保持**: sessionAttributesを活用
- **サイズ制限**: 100交換まで保持、古いものから削除

### 4. 環境変数の柔軟な管理

#### 複数の取得方法を実装
```python
# 1. 環境変数（Alexaコンソール）
api_key = os.environ.get('openai_api_key')

# 2. .envファイル（ローカルテスト）
if not api_key:
    # .envから読み込み

# 3. デフォルト値（非推奨）
if not api_key:
    api_key = ""
```

### 5. デバッグとトラブルシューティング

#### ローカルテストの重要性
```bash
# 直接APIテスト
python3 test_openai_api.py

# Lambda関数テスト
python3 test_lambda.py

# 会話フローテスト
python3 test_conversation_flow.py
```

#### CloudWatchログの活用
- APIキーの状態確認
- リクエスト/レスポンスの詳細
- エラーメッセージの完全な記録

### 6. インタラクションモデルの管理

#### 問題
- サンプル発話の重複によるFallbackIntent
- 勝手にサンプル数を削減（278→37）してユーザーから指摘

#### 教訓
- **既存のサンプルを勝手に削減しない**
- **重複チェックは慎重に実施**
- **変更は必ずユーザーに確認**

### 7. 会話継続機能の実装

#### 成功したアプローチ
- 短い返答（15文字未満）は文脈で解釈
- 最新10件の会話履歴をGPTに送信
- インテント別にコンテキスト推論

```python
if len(query) < 15:
    prompt = f"これまでの会話:\n{context}\n\n新しい質問: {query}\n\n重要: ユーザーの短い返答は、直前の会話の文脈で理解して答えてください。"
```

## 📊 プロジェクトメトリクス

| 指標 | 結果 |
|------|------|
| 対応インテント数 | 8種類 |
| サンプル発話数 | 400以上 |
| 会話履歴保持 | 100件まで |
| API応答時間 | 7秒以内 |
| テストカバレッジ | 主要フロー100% |

## 🚀 今後の改善提案

### 1. DynamoDB統合
- セッションを超えた会話履歴の永続化
- ユーザーごとの個人化

### 2. エラーハンドリングの強化
- APIレート制限への対応
- フォールバック応答の充実
- リトライメカニズム

### 3. パフォーマンス最適化
- レスポンスキャッシュ
- 非同期処理の導入
- ストリーミング応答

### 4. 監視とアラート
- CloudWatch Alarms設定
- エラー率のモニタリング
- 応答時間の追跡

## 📝 チェックリスト（今後のプロジェクトのために）

### プロジェクト開始時
- [ ] 最新のAPIドキュメントを確認
- [ ] 利用可能なモデルのリスト作成
- [ ] 制約事項（タイムアウト等）の確認
- [ ] テスト環境のセットアップ

### 実装時
- [ ] APIエンドポイントの正確性確認
- [ ] リクエスト/レスポンス形式の検証
- [ ] エラーハンドリングの実装
- [ ] ログ出力の充実

### テスト時
- [ ] ローカルテストの実施
- [ ] 本番環境との差異確認
- [ ] 会話フローのテスト
- [ ] エラーケースのテスト

### デプロイ時
- [ ] 環境変数の設定確認
- [ ] CloudWatchログの確認
- [ ] 実機での動作確認
- [ ] ドキュメントの更新

## 🙏 謝辞

ユーザーからの貴重なフィードバック、特にGPT-5の存在についての4回にわたる指摘に感謝します。この経験から、思い込みではなく事実に基づく判断の重要性を改めて学びました。

---

作成日: 2025-09-22
最終更新: 2025-09-22
プロジェクト: Alexa GenAI Assistant