# GenAI Alexa スキル - 完全セットアップガイド

## 現在の状態
✅ 日本語版・英語版ともに起動確認済み
✅ 基本的なインテント処理が動作
⚠️ GPT統合は未設定（APIキーが必要）

## 必要な修正と設定

### 1. 相互作用モデルの完全設定

#### 日本語版（ja-JP）
1. Alexaデベロッパーコンソール → 構築 → 言語タブ「Japanese (JP)」
2. JSONエディターに`lambda/interaction_model_ja.json`の内容を貼り付け
3. 保存 → ビルド

#### 英語版（en-US）
1. 言語タブ「English (US)」に切り替え
2. JSONエディターに`lambda/interaction_model_en.json`の内容を貼り付け
3. 保存 → ビルド

### 2. Lambda関数の設定

#### オプションA: テスト用（APIキーなし）
```python
# lambda_function_bilingual.py を使用
# 両言語対応、テスト応答のみ
```

#### オプションB: GPT統合版（APIキー必要）
```python
# lambda_function_gpt_ready.py を使用
# 13行目のAPIキーを設定:
api_key = "sk-xxx..."  # あなたのOpenAI APIキー

# モデルの選択（15行目）:
model = "gpt-4"  # または "gpt-3.5-turbo"
```

### 3. 必須ハンドラーの確認

以下のハンドラーがすべて実装されていることを確認：
- ✅ LaunchRequestHandler
- ✅ GptQueryIntentHandler
- ✅ HelpIntentHandler
- ✅ CancelOrStopIntentHandler
- ✅ FallbackIntentHandler（日本語版で必須）
- ✅ SessionEndedRequestHandler
- ✅ CatchAllExceptionHandler

### 4. 必須インテントの確認

両言語で以下のインテントが必要：
- GptQueryIntent（カスタム）
- AMAZON.FallbackIntent
- AMAZON.CancelIntent
- AMAZON.HelpIntent
- AMAZON.StopIntent
- AMAZON.NavigateHomeIntent

### 5. requirements.txt の確認

Lambda関数で必要なパッケージ：
```
ask-sdk-core==1.11.0
requests==2.31.0
```

### 6. 環境変数（オプション）

Lambda関数の環境変数でAPIキーを管理する場合：
```python
import os
api_key = os.environ.get('OPENAI_API_KEY', 'YOUR_API_KEY')
```

## トラブルシューティング

### 問題: 「すみません、お役に立てません」
**原因**: スキルが起動していない
**解決策**:
1. 呼び出し名が正しいか確認（日本語: じぇない、英語: gen ai）
2. AMAZON.FallbackIntentが追加されているか確認
3. エンドポイントが正しく設定されているか確認

### 問題: FallbackIntentが呼ばれる
**原因**: GptQueryIntentが認識されていない
**解決策**:
1. GptQueryIntentのサンプル発話を確認
2. スロット名が"query"になっているか確認
3. スロットタイプがAMAZON.SearchQueryか確認

### 問題: 英語版で日本語が返ってくる
**原因**: ロケール判定が機能していない
**解決策**: lambda_function_bilingual.pyまたはlambda_function_gpt_ready.pyを使用

### 問題: タイムアウトエラー
**原因**: OpenAI API呼び出しが遅い
**解決策**:
1. タイムアウト値を調整（5秒→10秒）
2. max_tokensを減らす（150→100）
3. モデルをgpt-3.5-turboに変更

## テストフレーズ

### 日本語
```
じぇないを開いて
人工知能について教えて
天気はどう
ストップ
```

### 英語
```
open gen ai
tell me about artificial intelligence
what's the weather
stop
```

## 次のステップ

1. **OpenAI APIキーの取得**
   - https://platform.openai.com/api-keys
   - 課金設定が必要

2. **高度な機能の追加**
   - 会話履歴の永続化
   - フォローアップ質問の生成
   - コンテキストのクリア機能

3. **パフォーマンス最適化**
   - レスポンスのキャッシング
   - 非同期処理の実装

4. **公開準備**
   - スキルアイコンの追加
   - 詳細説明の記入
   - プライバシーポリシーの作成
   - 利用規約の作成

## 重要な注意点

1. **APIキーの管理**
   - ハードコードは避ける
   - 環境変数またはAWS Secrets Managerを使用

2. **コスト管理**
   - OpenAI APIの使用量を監視
   - max_tokensを適切に設定
   - レート制限を実装

3. **エラーハンドリング**
   - API失敗時のフォールバック
   - タイムアウト処理
   - ユーザーフレンドリーなエラーメッセージ

## ファイル構成

```
alexa-genai/
├── lambda/
│   ├── lambda_function.py（オリジナル）
│   ├── lambda_function_bilingual.py（テスト用・両言語対応）
│   ├── lambda_function_gpt_ready.py（GPT統合版）
│   ├── interaction_model_ja.json（日本語モデル）
│   └── interaction_model_en.json（英語モデル）
├── skill-package/
│   ├── skill.json（スキルマニフェスト）
│   └── interactionModels/
│       └── custom/
│           ├── ja-JP.json
│           └── en-US.json
└── requirements.txt
```