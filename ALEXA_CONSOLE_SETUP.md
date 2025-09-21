# Alexa Developer Console 設定手順

## 重要：日本語スキルが起動しない問題の解決

### 前提条件の確認
1. Alexaアプリまたはデバイスの言語設定が「日本語」になっているか
2. テストする際のアカウントが日本のAmazonアカウントか

### Step 1: 言語設定の確認と追加

1. Alexa Developer Consoleにログイン
2. 該当スキルを選択
3. 「構築」タブを開く
4. 左メニューから「言語」を選択
5. 以下の言語が有効になっているか確認：
   - **日本語（日本）** - ja-JP
   - 英語（米国） - en-US

もし日本語が無い場合：
- 「言語を追加」をクリック
- 「日本語（日本）」を選択
- 追加する

### Step 2: 日本語の呼び出し名設定

1. **言語選択を「日本語（日本）」に切り替える**（重要！）
2. 左メニューから「呼び出し」→「スキルの呼び出し名」を選択
3. 以下を設定：
   ```
   呼び出し名: じぇない
   ```
   ※ひらがなで入力（カタカナではない）

### Step 3: 日本語の相互作用モデル設定

1. 言語選択が「日本語（日本）」になっていることを確認
2. 左メニューから「相互作用モデル」→「JSONエディター」を選択
3. 以下のJSONを貼り付け：

```json
{
    "interactionModel": {
        "languageModel": {
            "invocationName": "じぇない",
            "intents": [
                {
                    "name": "GptQueryIntent",
                    "slots": [
                        {
                            "name": "query",
                            "type": "AMAZON.SearchQuery"
                        }
                    ],
                    "samples": [
                        "{query} について教えて",
                        "{query} を教えて",
                        "{query} は何"
                    ]
                },
                {
                    "name": "AMAZON.CancelIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.HelpIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.StopIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.FallbackIntent",
                    "samples": []
                }
            ],
            "types": []
        }
    }
}
```

### Step 4: Lambda関数の設定

1. 「コード」タブを開く
2. `index.js`または`lambda_function.py`を開く
3. 以下の内容で置き換える：

```python
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "じぇないアシスタントへようこそ。何でも聞いてください。"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        query = slots["query"].value if slots and "query" in slots else "質問なし"

        speak_output = f"{query}について聞かれました。テスト応答です。"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("他に質問はありますか？")
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "何でも質問してください。例えば、天気について教えて、と言ってみてください。"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "さようなら！"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "すみません、よくわかりませんでした。もう一度お願いします。"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = "すみません、エラーが発生しました。"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
```

### Step 5: ビルドとデプロイ

1. 「モデルを保存」をクリック
2. 「モデルをビルド」をクリック
3. ビルド完了を待つ（2-3分）
4. 「コード」タブで「デプロイ」をクリック

### Step 6: テスト

1. 「テスト」タブを開く
2. テストを「開発中」に設定
3. **言語を「日本語（日本）」に設定**
4. 以下を入力してテスト：

```
じぇないを開いて
```

もしくは：
```
じぇないをひらいて
```

### トラブルシューティング

#### まだ「すみません、お役に立てません」が出る場合：

1. **エンドポイント設定の確認**
   - 「構築」タブ → 「エンドポイント」
   - AWS Lambda ARNが正しく設定されているか確認
   - デフォルトリージョンが設定されているか確認

2. **スキルIDの確認**
   - Lambda関数の環境変数でスキルIDの検証が有効になっている可能性
   - 「構築」タブの上部にあるスキルIDを確認

3. **CloudWatchログの確認**
   - AWS Console → CloudWatch → ログ
   - Lambda関数のログを確認
   - リクエストが到達しているか確認

4. **テストシミュレーターのリセット**
   - テストタブで「リセット」ボタンをクリック
   - 再度「じぇないを開いて」でテスト

### 重要な注意点

- **言語選択を必ず確認**：各設定画面で言語タブが「日本語（日本）」になっているか
- **呼び出し名は「ひらがな」**：「じぇない」（カタカナの「ジェナイ」ではない）
- **保存とビルド**：変更後は必ず「保存」→「ビルド」→「デプロイ」の順番で実行