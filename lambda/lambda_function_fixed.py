from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        try:
            # Get locale from request
            locale = handler_input.request_envelope.request.locale
            logger.info(f"Launch request received. Locale: {locale}")

            # Check if Japanese locale
            if locale and locale.startswith('ja'):
                speak_output = "GenAIアシスタントへようこそ。何か質問してください。"
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
        except Exception as e:
            logger.error(f"Error in LaunchRequestHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Error starting the skill")
                    .response
            )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for GPT Query Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        try:
            # Get locale
            locale = handler_input.request_envelope.request.locale
            logger.info(f"GptQueryIntent received. Locale: {locale}")

            # Get the query slot value
            slots = handler_input.request_envelope.request.intent.slots
            query = "no query"

            if slots and "query" in slots and slots["query"].value:
                query = slots["query"].value
                logger.info(f"Query received: {query}")

            # Check if Japanese
            if locale and locale.startswith('ja'):
                speak_output = f"「{query}」について質問されました。これはテスト応答です。スキルは正常に動作しています。"
                reprompt = "他に質問はありますか？"
            else:
                speak_output = f"You asked about {query}. This is a test response to confirm the skill is working."
                reprompt = "What else would you like to know?"

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        except Exception as e:
            logger.error(f"Error in GptQueryIntentHandler: {str(e)}")
            locale = handler_input.request_envelope.request.locale

            if locale and locale.startswith('ja'):
                speak_output = "申し訳ございません。エラーが発生しました。"
            else:
                speak_output = "Sorry, there was an error processing your request."

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "このスキルでは、どんな質問にもお答えします。例えば、「人工知能について教えて」と聞いてみてください。"
        else:
            speak_output = "You can ask me any question. Try saying 'tell me about artificial intelligence'."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        locale = handler_input.request_envelope.request.locale

        if locale and locale.startswith('ja'):
            speak_output = "ご利用ありがとうございました。さようなら！"
        else:
            speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
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
    """Generic error handling."""
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

# Build the skill
sb = SkillBuilder()

# Add request handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())  # Keep last

# Add exception handler
sb.add_exception_handler(CatchAllExceptionHandler())

# Lambda handler
lambda_handler = sb.lambda_handler()