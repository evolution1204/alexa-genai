# GenAI Assistant for Alexa

GPT-5を使用したAlexaスキル

## 機能
- GPT-5 (gpt-5-mini) との対話
- 日本語・英語完全対応
- 9つの専用インテント
  - 基本的な質問 (GptQueryIntent)
  - 創作・作成 (CreativeIntent)
  - エンタメ (EntertainmentIntent)
  - 感情的応答 (EmotionalIntent)
  - 分析・評価 (AnalysisIntent)
  - アドバイス (HelpIntent)
  - 哲学的思考 (PhilosophicalIntent)
  - 実践的ガイド (PracticalIntent)
  - 動作確認 (TestIntent)

## セットアップ

### 1. Lambda関数
1. AWS Lambdaで新しい関数を作成
2. `lambda/lambda_function.py`をアップロード
3. `lambda/requirements.txt`の依存関係をインストール
4. APIキーを設定（コード内の`api_key`変数）

### 2. Alexaスキル
1. Alexa開発者コンソールでスキルを作成
2. `skill-package/skill.json`の内容を適用
3. 各言語のインタラクションモデルを適用:
   - 日本語: `skill-package/interactionModels/custom/ja-JP.json`
   - 英語: `skill-package/interactionModels/custom/en-US.json`
4. Lambda関数のARNをエンドポイントに設定

### 3. 起動方法
- 日本語: 「アレクサ、じぇないを開いて」
- 英語: "Alexa, open gen ai"

## ファイル構成
```
alexa-genai/
├── lambda/
│   ├── lambda_function.py    # メインハンドラ
│   └── requirements.txt       # Python依存関係
├── skill-package/
│   ├── skill.json            # スキル設定
│   └── interactionModels/
│       └── custom/
│           ├── ja-JP.json    # 日本語モデル
│           └── en-US.json    # 英語モデル
└── README.md
```

## 注意事項
- APIキーは環境変数またはAWS Secrets Managerで管理推奨
- 個人利用のみ（本番環境では適切なエラーハンドリングとセキュリティ対策を実装）