"""
デバッグ用最小Lambda関数
エラーの原因を特定するために使用
"""

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
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
        logger.info("=== LaunchRequestHandler START ===")
        speak_output = "じぇないアシスタントへようこそ。何かお手伝いしましょうか？"
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
        logger.info("=== GptQueryIntentHandler START ===")
        try:
            # Get the query value
            query = handler_input.request_envelope.request.intent.slots["query"].value
            logger.info(f"Query: {query}")

            # Simple test response
            if "生成" in query or "AI" in query.upper():
                speak_output = "生成AIは、テキストや画像を自動的に作り出す人工知能技術です。テストモードで動作しています。"
            else:
                speak_output = f"「{query}」について質問されました。テストモードで動作しています。"

            logger.info(f"Response: {speak_output}")

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask("他に質問はありますか？")
                    .response
            )
        except Exception as e:
            logger.error(f"ERROR in GptQueryIntentHandler: {str(e)}", exc_info=True)
            return (
                handler_input.response_builder
                    .speak("エラーが発生しました。詳細はログを確認してください。")
                    .response
            )

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== FallbackIntentHandler TRIGGERED ===")
        speak_output = "すみません、よく分かりませんでした。もう一度お願いします。"
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
        speak_output = "さようなら"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info(f"Session ended: {handler_input.request_envelope.request.reason}")
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(f"=== EXCEPTION CAUGHT ===")
        logger.error(f"Exception: {str(exception)}", exc_info=True)

        speak_output = "予期しないエラーが発生しました。もう一度お試しください。"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("他に何かお手伝いしましょうか？")
                .response
        )

# スキルビルダー
sb = SkillBuilder()

# ハンドラーの登録
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()