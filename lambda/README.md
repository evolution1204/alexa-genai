# 🤖 Alexa GPT-5 Chat Lambda Function

## 概要

Amazon AlexaスキルとOpenAI GPT-5-chat-latestを統合した対話型AIアシスタント「ぴこ」のLambda関数実装です。

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
- GptQueryIntent
- CreativeIntent
- EntertainmentIntent
- EmotionalIntent
- AnalysisIntent
- HelpIntent
- PhilosophicalIntent
- PracticalIntent
- DetailRequestIntent
- NavigationIntent
- SelectionIntent

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
```python
1. ユーザー入力を受信（スロット値から取得）
2. デッドライン（5.6秒）チェック
3. OpenAI APIを呼び出し（3秒タイムアウト）
4. 成功時：応答を返却、履歴に追加
5. 失敗時：「続けて」メッセージでリトライを促す
```

### 2. 継続処理（ContinuationIntent）
```python
1. pending_promptがあればそれを使用
2. なければ最後のユーザー発話から継続プロンプトを生成
3. 「続きと詳細を短く」を付加して処理
```

### 3. 絞り込み処理（RefineIntent）
```python
1. フィルター条件をスロットから取得
2. 元のプロンプトに条件を追加
3. 「要点だけ短く」を付加して処理
```

## 🚀 デプロイ手順

### 1. Zipファイル作成
```bash
cd /home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/lambda
zip lambda-function.zip lambda_function.py utils.py
```

### 2. AWS Lambda更新
```bash
aws lambda update-function-code \
    --function-name AlexaGptSkill \
    --zip-file fileb://lambda-function.zip \
    --region us-west-2
```

### 3. 確認
```bash
aws lambda get-function --function-name AlexaGptSkill --region us-west-2 | grep LastModified
```

## 🧪 テストシナリオ

### 基本動作
```
「アレクサ、ぴこを開いて」
→ "ぴこだよ。なんでも聞いてみて！"

「AIについて教えて」
→ GPT-5の応答（50-100字程度）

「もっと詳しく」（ContinuationIntent）
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
「うん」「はい」（AcknowledgmentIntent）
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
lambda/
├── lambda_function.py  # メインハンドラー（344行）
├── utils.py           # OpenAI API設定（37行）
└── README.md          # このファイル
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

## 📈 パフォーマンス指標

| 指標 | 目標値 | 説明 |
|------|--------|------|
| 平均応答時間 | < 3秒 | OpenAI API呼び出し時間 |
| タイムアウト率 | < 10% | 3秒を超える応答の割合 |
| Lambda実行時間 | < 6秒 | 8秒制限に対して余裕を確保 |
| エラー率 | < 5% | API呼び出しの失敗率 |

## 🔄 更新履歴

### 2025-09-28（現在のバージョン）
- モデルを`gpt-5-chat-latest`に設定
- シンプルな同期処理設計に変更
- タイムアウトを5.6秒/3.0秒に最適化
- 相づち処理（AcknowledgmentIntent）を追加
- SSML安全化処理を強化

---

**メンテナー**: Claude Code
**最終更新**: 2025-09-28
**状態**: 本番稼働中 🟢