"""
最小限のテスト用Lambda関数
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
        try:
            # リクエストの詳細をログに記録
            request = handler_input.request_envelope.request
            logger.info(f"Request type: {request.object_type}")
            logger.info(f"Request locale: {request.locale}")

            # 日本語の場合
            if request.locale and request.locale.startswith("ja"):
                speak_output = "じぇないアシスタントのテストバージョンです。正常に動作しています。"
            else:
                speak_output = "This is a test version of Gen AI assistant. It's working correctly."

            logger.info(f"Response: {speak_output}")

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        except Exception as e:
            logger.error(f"ERROR in LaunchRequestHandler: {str(e)}", exc_info=True)
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
        speak_output = "フォールバックが呼ばれました。これはテストメッセージです。"
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

        speak_output = f"例外が発生しました: {str(exception)[:50]}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

# スキルビルダー
sb = SkillBuilder()

# ハンドラーの登録
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()