# 🤖 Alexa GPT-5 Chat Assistant

Amazon AlexaスキルとOpenAI GPT-5-chat-latestを統合した対話型AIアシスタント「ぴこ」

## 📋 現在の実装状況

### モデル設定
```python
OPENAI_MODEL = "gpt-5-chat-latest"  # 現在使用中のモデル
```

### タイムアウト設定
```python
HARD_DEADLINE_SEC = 5.6  # Lambda処理の最大時間
HTTP_TIMEOUT_SEC = 3.0   # OpenAI API呼び出しのタイムアウト
MAX_HISTORY_TURNS = 6    # 保持する会話履歴のターン数（6往復分）
```

### キャラクター設定

「ぴこ」は元気で可愛い相棒アシスタントとして設定：
- 一人称：「ぼく」
- 語尾：やわらかく（〜だよ/〜だね/〜かな）
- 最初は50〜100字で要点を伝える
- 絵文字・顔文字・URLは使用しない
- 具体例は短く提供
- 必要に応じて次の提案を一言添える

## 🏗️ アーキテクチャ

### シンプルな同期処理設計
- ThreadPoolExecutorを使用せず、同期的にOpenAI APIを呼び出し
- タイムアウト時は即座に「続けて」メッセージを返却
- Lambda 8秒制限に対して2.4秒の余裕を確保

### SSML安全化処理
- 制御文字の削除
- URLを「リンク」に置換
- 絵文字の除去（TTS互換性のため）
- 改行をSSMLの`<break>`タグに変換
- 句点の自動付与（無音回避）

## 📝 対応インテント

### メインクエリインテント
以下のインテントはすべて`GenericQueryIntentsHandler`で処理：
- GptQueryIntent - 基本的な質問
- CreativeIntent - 創作・作成
- EntertainmentIntent - エンタメ
- EmotionalIntent - 感情的応答
- AnalysisIntent - 分析・評価
- HelpIntent - アドバイス
- PhilosophicalIntent - 哲学的思考
- PracticalIntent - 実践的ガイド
- DetailRequestIntent - 詳細リクエスト
- NavigationIntent - ナビゲーション
- SelectionIntent - 選択

### 特殊インテント
- **RefineIntent**: 条件を追加して絞り込み
- **ContinuationIntent**: 会話の続きや詳細を要求
- **AcknowledgmentIntent**: 相づち（「うん」「はい」など）→継続として処理
- **TestIntent**: 動作確認用

### システムインテント
- **AMAZON.HelpIntent**: 使い方の説明
- **AMAZON.StopIntent/CancelIntent**: スキル終了
- **AMAZON.NavigateHomeIntent**: ホームに戻る
- **AMAZON.FallbackIntent**: 聞き取れなかった場合
- **AMAZON.YesIntent**: 肯定応答（継続として処理）

## 🔄 会話フロー

### 1. 通常の質問処理
```
1. ユーザー入力を受信（スロット値から取得）
2. デッドライン（5.6秒）チェック
3. OpenAI APIを呼び出し（3秒タイムアウト）
4. 成功時：応答を返却、履歴に追加
5. 失敗時：「続けて」メッセージでリトライを促す
```

### 2. 継続処理（ContinuationIntent）
```
1. pending_promptがあればそれを使用
2. なければ最後のユーザー発話から継続プロンプトを生成
3. 「続きと詳細を短く」を付加して処理
```

### 3. 絞り込み処理（RefineIntent）
```
1. フィルター条件をスロットから取得
2. 元のプロンプトに条件を追加
3. 「要点だけ短く」を付加して処理
```

## 🚀 セットアップ

### 1. APIキーの設定

#### 方法A: Alexa開発者コンソール（簡単）
1. [Alexa開発者コンソール](https://developer.amazon.com/alexa/console/ask)にログイン
2. スキルを選択 → 「コード」タブ
3. `utils.py`の6行目を編集:
   ```python
   _OPENAI_API_KEY = "sk-proj-あなたのAPIキー"
   ```
4. 「デプロイ」ボタンをクリック

#### 方法B: AWS Lambda環境変数（推奨）
1. AWS Lambdaコンソール → 設定 → 環境変数
2. キー: `OPENAI_API_KEY`
3. 値: あなたのAPIキー

### 2. デプロイ手順

#### AWS CLIを使用する場合
```bash
# Zipファイル作成
cd lambda
zip lambda-function.zip lambda_function.py utils.py

# Lambda関数を更新
aws lambda update-function-code \
    --function-name AlexaGptSkill \
    --zip-file fileb://lambda-function.zip \
    --region us-west-2
```

### 3. スキルの起動
- 日本語: 「アレクサ、ぴこを開いて」
- 英語: "Alexa, open pico assistant"

## 🧪 テストシナリオ

### 基本動作
```
「アレクサ、ぴこを開いて」
→ "ぴこだよ。なんでも聞いてみて！"

「AIについて教えて」
→ GPT-5の応答（50-100字程度）

「もっと詳しく」
→ 詳細な説明が返る
```

### タイムアウト処理
```
長い処理が必要な質問
→ "ごめん、いまはうまく答えを取れなかった。『続けて』で試せるよ。"

「続けて」
→ 再処理して応答
```

### 相づち処理
```
「うん」「はい」
→ 前の話題の続きとして処理
```

## 📊 設定値の詳細

| 設定項目 | 値 | 説明 |
|---------|-----|------|
| HARD_DEADLINE_SEC | 5.6秒 | Lambda処理の最大時間（8秒制限に対して2.4秒の余裕） |
| HTTP_TIMEOUT_SEC | 3.0秒 | OpenAI API呼び出しのタイムアウト |
| MAX_HISTORY_TURNS | 6 | 会話履歴の保持数（6往復=12メッセージ） |
| _MAX_TOKENS | 120 | OpenAI応答の最大トークン数 |
| SSML最大長 | 7000文字 | Alexa制限（8000）に対して余裕を持たせた値 |

## 📁 ファイル構成

```
alexa-genai/
├── lambda/
│   ├── lambda_function.py  # メインハンドラー（344行）
│   ├── utils.py            # OpenAI API設定（37行）
│   └── requirements.txt    # 依存関係
├── skill-package/
│   ├── skill.json          # スキル設定
│   └── interactionModels/
│       └── custom/
│           ├── ja-JP.json  # 日本語モデル
│           └── en-US.json  # 英語モデル
└── README.md              # このファイル
```

### lambda_function.py の構成
- **1-99行**: インポートと設定、SSML処理
- **100-131行**: ユーティリティ関数（履歴管理、メッセージ構築）
- **133-341行**: 各種ハンドラー実装
- **342-344行**: SkillBuilderの設定とエクスポート

### utils.py の構成
- OpenAI クライアント初期化
- Chat Completions API呼び出し（エラー時は空文字を返却）
- APIキーは直接記載（本番環境ではSecrets Manager推奨）

## ⚠️ 注意事項

### セキュリティ
- **APIキー管理**: utils.pyにAPIキーが直接記載されています
  - 本番環境では環境変数またはAWS Secrets Managerの使用を推奨

### パフォーマンス
- **タイムアウト設計**: Lambda 8秒制限に対して十分な余裕（2.4秒）
- **履歴制限**: 6往復分のみ保持してコンテキストサイズを制御
- **応答長制限**: 120トークンで音声出力に最適化

### 現在の制限事項
- DynamoDBは使用していない（セッション属性のみ）
- 会話履歴はセッション終了で消失
- エラー時のリトライは手動（「続けて」と言う必要あり）

## 🔍 トラブルシューティング

### よくある問題

#### 1. タイムアウトエラー
**症状**: 「続けて」メッセージが頻発
**原因**: OpenAI APIの応答が3秒を超過
**対策**: HTTP_TIMEOUT_SECを調整（ただしLambda 8秒制限に注意）

#### 2. 応答が短すぎる
**症状**: 詳細な説明が返らない
**原因**: _MAX_TOKENS = 120の制限
**対策**: utils.pyの_MAX_TOKENSを増やす（音声出力の長さに注意）

#### 3. 会話の文脈が失われる
**症状**: 前の話題を覚えていない
**原因**: MAX_HISTORY_TURNS = 6の制限
**対策**: 必要に応じて増やす（ただしトークン数に注意）

#### 4. APIキーエラー
**症状**: エラーが発生する
**確認事項**:
- APIキーが正しく設定されているか
- ダブルクォートで囲まれているか
- スペースが含まれていないか

#### 5. CloudWatchログが見れない
Lambda関数のロググループを確認:
- ロググループ名: `/aws/lambda/AlexaGptSkill`
- リージョン: us-west-2（オレゴン）

## 📈 パフォーマンス指標

| 指標 | 目標値 | 説明 |
|------|--------|------|
| 平均応答時間 | < 3秒 | OpenAI API呼び出し時間 |
| タイムアウト率 | < 10% | 3秒を超える応答の割合 |
| Lambda実行時間 | < 6秒 | 8秒制限に対して余裕を確保 |
| エラー率 | < 5% | API呼び出しの失敗率 |

## テスト済み環境
- AWS Lambda Python 3.8
- GPT-5-chat-latest
- ask-sdk-core 1.19.0
- openai 1.0+

## 🔄 更新履歴

### 2025-09-28（現在のバージョン）
- モデルを`gpt-5-chat-latest`に設定
- シンプルな同期処理設計に変更
- タイムアウトを5.6秒/3.0秒に最適化
- 相づち処理（AcknowledgmentIntent）を追加
- SSML安全化処理を強化

### 2025-09-22
- 初期バージョンリリース
- GPT-5-miniから移行
- 会話履歴機能の実装
- 9つの専用インテント対応

## ライセンス
MIT License
