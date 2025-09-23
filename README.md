# GenAI Assistant for Alexa

GPT-5を使用した高性能なAlexaスキル

## 🎯 最新アップデート (2025-09-22)

### 改善された新バージョン
- **完全ログ機能**: リクエスト/レスポンスの詳細ロギング
- **エラーハンドリング強化**: より詳細なエラー情報とフォールバック
- **GPT-5-mini対応**: 高速レスポンス（6秒以内）
- **SSML安全処理**: Alexaの音声出力を最適化
- **会話履歴保持**: 100件まで文脈を記憶

## 機能
- **GPT-5 (gpt-5-mini)** との対話
- 日本語・英語完全対応
- **会話履歴機能**: 文脈を保持した連続会話が可能
- 9つの専用インテント
  - 基本的な質問 (GptQueryIntent)
  - 創作・作成 (CreativeIntent)
  - エンタメ (EntertainmentIntent)
  - 感情的応答 (EmotionalIntent)
  - 分析・評価 (AnalysisIntent)
  - アドバイス (HelpIntent)
  - 哲学的思考 (PhilosophicalIntent)
  - 実践的ガイド (PracticalIntent)
  - 詳細リクエスト (DetailRequestIntent) **NEW**

## セットアップ

### 1. Alexaコンソールでの設定（推奨）
1. [Alexa開発者コンソール](https://developer.amazon.com/alexa/console/ask)にログイン
2. 「GenAI Assistant」スキルを選択（または新規作成）
3. 「コード」タブをクリック
4. `lambda/lambda_function.py`の内容を貼り付け
5. 34行目のAPIキーを設定:
   ```python
   OPENAI_API_KEY_DIRECT = "sk-proj-あなたのAPIキー"
   ```
6. 「デプロイ」ボタンをクリック

### 2. 環境変数での設定（本番推奨）
AWS Lambdaコンソールで:
1. 設定 → 環境変数
2. キー: `OPENAI_API_KEY`
3. 値: あなたのAPIキー

### 3. 起動方法
- 日本語: 「アレクサ、じぇないを開いて」
- 英語: "Alexa, open gen ai"

## ファイル構成
```
alexa-genai/
├── lambda/
│   ├── lambda_function.py          # メインハンドラ（改善版）
│   ├── lambda_function_simple.py   # シンプル版
│   ├── lambda_function_minimal.py  # 最小版（テスト用）
│   └── lambda_function_no_requests.py # urllib版
├── skill-package/
│   ├── skill.json            # スキル設定
│   └── interactionModels/
│       └── custom/
│           ├── ja-JP.json    # 日本語モデル
│           └── en-US.json    # 英語モデル
├── ALEXA_DEPLOYMENT_GUIDE.md  # デプロイ手順書
├── CLOUDWATCH_ACCESS_ISSUE.md # トラブルシューティング
└── README.md
```

## テスト済み環境
- AWS Lambda Python 3.8
- GPT-5-mini (Responses API)
- ask-sdk-core 1.19.0
- requests 2.31.0

## トラブルシューティング

### エラーが発生する場合
1. APIキーが正しく設定されているか確認
2. ダブルクォートで囲まれているか確認
3. スペースが含まれていないか確認

### CloudWatchログが見れない場合
`CLOUDWATCH_ACCESS_ISSUE.md`を参照してください。

### レスポンスが遅い場合
GPT-5-miniは`reasoning.effort: "low"`設定で6秒以内に応答するよう最適化されています。

## 使用例
```
ユーザー: じぇないを開いて
Alexa: じぇないアシスタントへようこそ。質問をどうぞ。

ユーザー: 生成AIとは？
Alexa: 生成AIは、大量のデータを学習して新しいテキスト、画像、音声などのコンテンツを作成する人工知能技術です。

ユーザー: もっと詳しく
Alexa: [前の会話の文脈を踏まえて詳細を説明]
```

## 注意事項
- APIキーは環境変数またはAWS Secrets Managerで管理推奨
- 本番環境では適切なセキュリティ対策を実装してください
- タイムアウトは6秒に設定（Alexaの8秒制限内）

## ライセンス
MIT License

## 作成者
Claude Code & User

---
最終更新: 2025-09-22