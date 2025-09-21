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
        # Get locale from request
        locale = handler_input.request_envelope.request.locale
        logger.info(f"Launch request received. Locale: {locale}")

        # Check if Japanese locale
        if locale and locale.startswith('ja'):
            speak_output = "じぇないアシスタントへようこそ。どんな質問でもどうぞ。"
            reprompt = "何について知りたいですか？"
        else:
            speak_output = "Welcome to Gen AI assistant. How can I help you today?"
            reprompt = "What would you like to know?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )

class TestIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("TestIntent")(handler_input)

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "テストインテントが正常に動作しています。"
            reprompt = "他に何か質問はありますか？"
        else:
            speak_output = "Test intent is working correctly."
            reprompt = "What else would you like to know?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        slots = handler_input.request_envelope.request.intent.slots
        query = "no query"

        if slots and "query" in slots and slots["query"].value:
            query = slots["query"].value
            logger.info(f"Query received: {query}")

        if locale and locale.startswith('ja'):
            speak_output = f"「{query}」について質問されました。これはテスト応答です。実際のGPT統合は後ほど追加されます。"
            reprompt = "他に質問はありますか？"
        else:
            speak_output = f"You asked about {query}. This is a test response. GPT integration will be added later."
            reprompt = "What else would you like to know?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "このスキルでは、どんな質問にも答えます。例えば、「人工知能について教えて」と聞いてみてください。"
        else:
            speak_output = "You can ask me any question. Try saying 'tell me about artificial intelligence'."

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
        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "ご利用ありがとうございました。さようなら！"
        else:
            speak_output = "Goodbye! Thanks for using Gen AI."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info(f"FallbackIntent triggered. Locale: {locale}")

        if locale and locale.startswith('ja'):
            speak_output = "すみません、よくわかりませんでした。もう一度お願いします。"
        else:
            speak_output = "Sorry, I didn't understand that. Could you please try again?"

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
        logger.info(f"Session ended: {handler_input.request_envelope.request.reason}")
        return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        locale = handler_input.request_envelope.request.locale

        logger.info(f"IntentReflector triggered for: {intent_name}")

        if locale and locale.startswith('ja'):
            speak_output = f"インテント「{intent_name}」が呼び出されました。"
        else:
            speak_output = f"You just triggered {intent_name}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(f"Exception: {exception}", exc_info=True)

        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "申し訳ございません。エラーが発生しました。もう一度お試しください。"
        else:
            speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# スキルビルダー
sb = SkillBuilder()

# ハンドラーの登録（順序が重要！）
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(TestIntentHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# IntentReflectorは最後に追加（デバッグ用）
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()