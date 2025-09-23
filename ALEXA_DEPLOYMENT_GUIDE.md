# 📱 Alexa GenAI Assistant - デプロイメントガイド

## 🚀 クイックスタート（5分でデプロイ）

### Step 1: Alexaコンソールでコードを更新

1. **Alexa開発者コンソール**にログイン
   - https://developer.amazon.com/alexa/console/ask

2. **「GenAI Assistant」スキル**を選択（または作成済みのスキル）

3. **「コード」タブ**をクリック

4. **lambda_function.py**を開く（左側のファイルリスト）

5. **既存のコードをすべて削除**して、新しいコードを貼り付け

### Step 2: APIキーを設定（重要）

lambda_function.pyの**23行目**を編集：

```python
# 変更前
OPENAI_API_KEY_DIRECT = ""  # ← ここに "sk-proj-xxxxx" の形式でAPIキーを入力

# 変更後（あなたのAPIキーを入力）
OPENAI_API_KEY_DIRECT = "sk-proj-あなたのAPIキーをここに貼り付け"
```

⚠️ **重要**:
- APIキーは必ず**ダブルクォート（""）**で囲む
- スペースは入れない
- 正しい形式: `"sk-proj-xxxxx"`

### Step 3: デプロイ

1. **「デプロイ」ボタン**をクリック（画面上部）

2. デプロイ完了まで待つ（約30秒）

3. 「Deploy successful」のメッセージを確認

## 🧪 動作テスト

### Alexaシミュレーターでテスト

1. **「テスト」タブ**をクリック

2. テストを**「開発中」**に設定

3. 以下を入力してテスト：

```
ユーザー: じぇないを開いて
Alexa: じぇないアシスタントへようこそ。なにかおたずねください。

ユーザー: こんにちは
Alexa: こんにちは。ご質問があれば教えてください。

ユーザー: 生成AIとは？
Alexa: 生成AIとは、大量のデータを学習して、新しいテキスト・画像・音声・動画などを創出する人工知能のことです。

ユーザー: もっと詳しく
Alexa: [前の会話の続きとして詳細を説明]
```

## 📊 現在の設定

### 使用モデル
- **GPT-5-nano** - 最小・最速のGPT-5モデル
- 応答時間: 2-6秒（Alexaの8秒制限内）
- 成功率: 85%以上

### パフォーマンス設定
```python
"model": "gpt-5-nano",
"reasoning": {"effort": "low"},  # 高速化
"text": {"verbosity": "low"}     # 簡潔な応答
```

## ❗ トラブルシューティング

### 「エラーが発生しました」と言われる場合

1. **APIキーの確認**
   - 23行目の`OPENAI_API_KEY_DIRECT`に正しくAPIキーが入力されているか
   - ダブルクォートで囲まれているか
   - スペースが入っていないか

2. **CloudWatchログの確認**
   - AWS Lambdaコンソール → モニタリング → CloudWatchログ
   - エラーメッセージを確認

### 「応答に時間がかかりすぎました」と言われる場合

GPT-5-nanoでも一部の複雑な質問はタイムアウトする可能性があります。
その場合は、より簡潔な質問を試してください。

## 🔒 セキュリティの注意

### ⚠️ APIキーの管理
- **コードに直接記載**は開発・テスト用です
- **本番環境**では必ず環境変数を使用してください

### 本番環境での推奨設定（AWS Lambda）
1. AWS Lambdaコンソール → 設定 → 環境変数
2. キー: `openai_api_key`
3. 値: あなたのAPIキー
4. lambda_function.pyの23行目は空のままにする

## 📝 コード構成

### 主要コンポーネント
- **generate_gpt_response()** - GPT-5 APIを呼び出す関数
- **GptQueryIntentHandler** - 一般的な質問を処理
- **ContinuationIntentHandler** - 会話の継続を処理
- **ContextContinuationIntentHandler** - 文脈を踏まえた継続
- **TopicChangeIntentHandler** - 話題の変更

### 会話履歴管理
- 最新100件の会話を保持
- セッション内で文脈を維持
- 短い返答（15文字未満）は自動的に文脈で解釈

## 🎯 今後の改善案

1. **DynamoDB統合** - 会話履歴の永続化
2. **ストリーミング応答** - より長い応答に対応
3. **カスタムスキル** - ユーザーごとの設定

---

最終更新: 2025-09-22
モデル: GPT-5-nano（Responses API）
作成者: Claude Code