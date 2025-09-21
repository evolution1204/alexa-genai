from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import requests
import logging
import json
import re

# Set your OpenAI API key
api_key = "YOUR_API_KEY"  # ← ここにAPIキーを設定

# GPT model - Using GPT-4 as GPT-5 is not yet available
model = "gpt-4"  # GPT-4を使用（GPT-5はまだ利用不可）

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def detect_language(text):
    """Simple language detection based on character analysis"""
    if not text:
        return 'en'

    # Check for Japanese characters (Hiragana, Katakana, Kanji)
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    if japanese_pattern.search(text):
        return 'ja'

    # Default to English
    return 'en'

def get_localized_message(key, locale='en'):
    """Get localized messages based on locale"""
    messages = {
        'en': {
            'welcome': "Welcome to Gen AI assistant. How can I help you today?",
            'goodbye': "Thank you for using Gen AI assistant. Goodbye!",
            'error': "Sorry, I had trouble doing what you asked. Please try again.",
            'reprompt': "You can ask me another question or say stop to end the conversation.",
            'reprompt_with_followup': "You can ask me another question, say 'next' to hear more suggestions, or say stop to end the conversation.",
            'followup_intro': "You could ask: ",
            'followup_outro': ". What would you like to know?",
            'clear_context': "I've cleared our conversation history. What would you like to talk about?",
            'default_followup_1': "Tell me more",
            'default_followup_2': "Give me an example",
            'help': "You can ask me any question. Try saying 'tell me about artificial intelligence'."
        },
        'ja': {
            'welcome': "じぇないアシスタントへようこそ。何かお手伝いしましょうか？",
            'goodbye': "ご利用いただきありがとうございました。さようなら！",
            'error': "申し訳ございません。エラーが発生しました。もう一度お試しください。",
            'reprompt': "他に質問がありましたらどうぞ。終了する場合は「ストップ」と言ってください。",
            'reprompt_with_followup': "他に質問がありましたらどうぞ。提案を聞く場合は「次」、終了する場合は「ストップ」と言ってください。",
            'followup_intro': "こんな質問はいかがですか: ",
            'followup_outro': "。何か知りたいことはありますか？",
            'clear_context': "会話履歴をクリアしました。何についてお話ししましょうか？",
            'default_followup_1': "詳しく教えて",
            'default_followup_2': "例を教えて",
            'help': "どんな質問にもお答えします。例えば、「人工知能について教えて」と聞いてみてください。"
        }
    }

    locale_messages = messages.get(locale, messages['en'])
    return locale_messages.get(key, messages['en'].get(key, 'Message not found'))

def get_device_locale(handler_input):
    """Get the device locale from the request"""
    try:
        locale = handler_input.request_envelope.request.locale
        # Extract language code (e.g., 'ja' from 'ja-JP')
        lang_code = locale.split('-')[0] if locale else 'en'
        return lang_code if lang_code in ['ja', 'en'] else 'en'
    except:
        return 'en'

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        locale = get_device_locale(handler_input)
        speak_output = get_localized_message('welcome', locale)

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        session_attr["device_locale"] = locale

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        try:
            # Get the query from the slot
            slots = handler_input.request_envelope.request.intent.slots
            query = "no query"

            if slots and "query" in slots and slots["query"].value:
                query = slots["query"].value
                logger.info(f"Query received: {query}")

            session_attr = handler_input.attributes_manager.session_attributes

            # Get or detect language
            device_locale = session_attr.get("device_locale", get_device_locale(handler_input))
            query_lang = detect_language(query)

            # Use query language if Japanese is detected, otherwise use device locale
            locale = query_lang if query_lang == 'ja' else device_locale
            session_attr["current_locale"] = locale

            if "chat_history" not in session_attr:
                session_attr["chat_history"] = []

            # Check if API key is configured
            if api_key == "YOUR_API_KEY":
                # Return a test response if API key is not configured
                if locale == 'ja':
                    response_text = f"「{query}」について質問されました。これはテスト応答です。OpenAI APIキーを設定すると、実際のGPT応答が有効になります。"
                else:
                    response_text = f"You asked about {query}. This is a test response. Configure your OpenAI API key to enable actual GPT responses."
            else:
                # Generate actual GPT response
                response_text = generate_gpt_response(session_attr["chat_history"], query, locale)
                # Update conversation history
                session_attr["chat_history"].append((query, response_text))

            # Prepare response with reprompt
            reprompt_text = get_localized_message('reprompt', locale)

            return (
                handler_input.response_builder
                    .speak(response_text)
                    .ask(reprompt_text)
                    .response
            )

        except Exception as e:
            logger.error(f"Error in GptQueryIntentHandler: {str(e)}", exc_info=True)
            locale = get_device_locale(handler_input)
            error_message = get_localized_message('error', locale)

            return (
                handler_input.response_builder
                    .speak(error_message)
                    .ask(error_message)
                    .response
            )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        locale = get_device_locale(handler_input)
        speak_output = get_localized_message('help', locale)

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
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("current_locale", get_device_locale(handler_input))
        speak_output = get_localized_message('goodbye', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        locale = get_device_locale(handler_input)
        logger.info(f"FallbackIntent triggered. Locale: {locale}")

        if locale == 'ja':
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
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info(f"Session ended: {handler_input.request_envelope.request.reason}")
        return handler_input.response_builder.response

class ClearContextIntentHandler(AbstractRequestHandler):
    """Handler for clearing conversation context."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ClearContextIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("current_locale", get_device_locale(handler_input))

        session_attr["chat_history"] = []
        session_attr["last_context"] = None

        speak_output = get_localized_message('clear_context', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(f"Exception: {exception}", exc_info=True)

        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("current_locale", get_device_locale(handler_input))
        speak_output = get_localized_message('error', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def generate_gpt_response(chat_history, new_question, locale='en'):
    """Generates a GPT response to a question"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        url = "https://api.openai.com/v1/chat/completions"

        # Create system message based on language
        if locale == 'ja':
            system_message = "あなたは親切なアシスタントです。簡潔に答えてください。"
        else:
            system_message = "You are a helpful assistant. Keep answers brief."

        messages = [{"role": "system", "content": system_message}]

        # Include conversation history (last 5 exchanges)
        for question, answer in chat_history[-5:]:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})

        # Add the new question
        messages.append({"role": "user", "content": new_question})

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=5)
        response_data = response.json()

        if response.ok:
            return response_data['choices'][0]['message']['content']
        else:
            logger.error(f"OpenAI API error: {response_data}")
            if locale == 'ja':
                return "申し訳ございません。APIエラーが発生しました。"
            else:
                return "Sorry, there was an API error."

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        if locale == 'ja':
            return "申し訳ございません。応答の生成中にエラーが発生しました。"
        else:
            return "Sorry, there was an error generating the response."

# Skill Builder
sb = SkillBuilder()

# Add request handlers in order
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(ClearContextIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Add exception handler
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()