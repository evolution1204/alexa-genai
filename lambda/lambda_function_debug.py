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
import os
import traceback

# Set your OpenAI API key - IMPORTANT: Replace with your actual API key
api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")

# GPT-5 model - choose from gpt-5, gpt-5-mini, or gpt-5-nano
# Note: If GPT-5 is not available, use gpt-4 as fallback
model = "gpt-4"  # Using GPT-4 as fallback if GPT-5 is not available

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
            'welcome': "GenAI assistant activated. How can I help you today?",
            'goodbye': "Thank you for using GenAI assistant. Goodbye!",
            'error': "Sorry, I had trouble doing what you asked. Please try again.",
            'reprompt': "You can ask me another question or say stop to end the conversation.",
            'reprompt_with_followup': "You can ask me another question, say 'next' to hear more suggestions, or say stop to end the conversation.",
            'followup_intro': "You could ask: ",
            'followup_outro': ". What would you like to know?",
            'clear_context': "I've cleared our conversation history. What would you like to talk about?",
            'default_followup_1': "Tell me more",
            'default_followup_2': "Give me an example"
        },
        'ja': {
            'welcome': "GenAIアシスタントが起動しました。何かお手伝いしましょうか？",
            'goodbye': "GenAIアシスタントをご利用いただきありがとうございました。さようなら！",
            'error': "申し訳ございません。エラーが発生しました。もう一度お試しください。",
            'reprompt': "他に質問がありましたらどうぞ。終了する場合は「ストップ」と言ってください。",
            'reprompt_with_followup': "他に質問がありましたらどうぞ。提案を聞く場合は「次」、終了する場合は「ストップ」と言ってください。",
            'followup_intro': "こんな質問はいかがですか: ",
            'followup_outro': "。何か知りたいことはありますか？",
            'clear_context': "会話履歴をクリアしました。何についてお話ししましょうか？",
            'default_followup_1': "詳しく教えて",
            'default_followup_2': "例を教えて"
        }
    }

    locale_messages = messages.get(locale, messages['en'])
    return locale_messages.get(key, messages['en'][key])

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
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            logger.info("LaunchRequestHandler invoked")
            locale = get_device_locale(handler_input)
            speak_output = get_localized_message('welcome', locale)

            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["chat_history"] = []
            session_attr["device_locale"] = locale

            logger.info(f"Launch successful, locale: {locale}")
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        except Exception as e:
            logger.error(f"Error in LaunchRequestHandler: {str(e)}")
            logger.error(traceback.format_exc())
            return (
                handler_input.response_builder
                    .speak("Sorry, there was an error starting the skill.")
                    .response
            )

def generate_followup_questions(chat_history, question, answer, locale='en'):
    """Generate contextual follow-up questions based on the conversation"""
    followup_questions = []

    # Language-specific follow-up patterns
    if locale == 'ja':
        patterns = [
            "もっと詳しく教えて",
            "具体的な例を教えて",
            "他の方法はある？",
            "なぜそうなるの？",
            "どうすればいい？"
        ]
    else:
        patterns = [
            "Tell me more about this",
            "Can you give me an example?",
            "What are the alternatives?",
            "Why is that?",
            "How can I apply this?"
        ]

    # Select 2-3 relevant follow-up questions
    import random
    followup_questions = random.sample(patterns, min(3, len(patterns)))

    return followup_questions

def generate_response_from_claude(new_question, chat_history=[], locale='en'):
    """Generate response using OpenAI API (GPT-4 as fallback)"""
    logger.info(f"Generating response for: {new_question}")
    logger.info(f"Using API key: {'configured' if api_key != 'YOUR_API_KEY' else 'NOT SET'}")

    if api_key == "YOUR_API_KEY":
        logger.error("API key not configured!")
        return "Please configure your OpenAI API key in the Lambda function.", []

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {
            "role": "system",
            "content": f"You are a helpful AI assistant. Respond in {locale if locale == 'ja' else 'English'}. Keep responses concise and suitable for voice output (under 200 words)."
        }
    ]

    # Include limited chat history for context (last 3 exchanges)
    history_limit = 3
    for question, answer in chat_history[-history_limit:]:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})

    # Add the new question
    messages.append({"role": "user", "content": new_question})

    data = {
        "model": "gpt-4",  # Using GPT-4 as fallback
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        logger.info(f"Sending request to OpenAI API with model: {data['model']}")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        logger.info(f"Response status code: {response.status_code}")

        response_data = response.json()

        if response.ok:
            response_text = response_data['choices'][0]['message']['content']
            logger.info(f"Successfully generated response: {response_text[:100]}...")

            # Generate follow-up questions for the response
            try:
                followup_questions = generate_followup_questions(
                    chat_history + [(new_question, response_text)],
                    new_question,
                    response_text,
                    locale
                )
                logger.info(f"Generated follow-up questions: {followup_questions}")
            except Exception as e:
                logger.error(f"Error generating follow-up questions: {str(e)}")
                followup_questions = []

            return response_text, followup_questions
        else:
            error_msg = response_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"API error: {error_msg}")
            return f"API Error: {error_msg}", []

    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return "The request took too long. Please try again.", []
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error: {str(e)}", []

class ClearContextIntentHandler(AbstractRequestHandler):
    """Handler for clearing conversation context."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ClearContextIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            session_attr = handler_input.attributes_manager.session_attributes
            locale = session_attr.get("device_locale", get_device_locale(handler_input))

            # Clear the chat history
            session_attr["chat_history"] = []
            session_attr["pending_followups"] = []

            speak_output = get_localized_message('clear_context', locale)

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(get_localized_message('reprompt', locale))
                    .response
            )
        except Exception as e:
            logger.error(f"Error in ClearContextIntentHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Sorry, there was an error.")
                    .response
            )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for GPT Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            logger.info("GptQueryIntentHandler invoked")

            # Get the query slot value
            slots = handler_input.request_envelope.request.intent.slots
            if slots and "query" in slots and slots["query"].value:
                query = slots["query"].value
                logger.info(f"Query received: {query}")
            else:
                logger.error("No query slot value found")
                return (
                    handler_input.response_builder
                        .speak("I didn't catch that. Please ask me a question.")
                        .ask("What would you like to know?")
                        .response
                )

            # Get session attributes
            session_attr = handler_input.attributes_manager.session_attributes
            chat_history = session_attr.get("chat_history", [])

            # Detect language from query
            detected_lang = detect_language(query)
            device_locale = session_attr.get("device_locale", get_device_locale(handler_input))
            locale = detected_lang if detected_lang == 'ja' else device_locale

            logger.info(f"Processing query with locale: {locale}")

            # Generate response
            response_text, followup_questions = generate_response_from_claude(query, chat_history, locale)

            # Add to chat history
            chat_history.append((query, response_text))
            session_attr["chat_history"] = chat_history[-10:]  # Keep last 10 exchanges
            session_attr["pending_followups"] = followup_questions

            # Create response with follow-up suggestions if available
            if followup_questions and len(followup_questions) > 0:
                followup_text = get_localized_message('followup_intro', locale) + followup_questions[0] + get_localized_message('followup_outro', locale)
                speak_output = f"{response_text} ... {followup_text}"
                reprompt_text = get_localized_message('reprompt_with_followup', locale)
            else:
                speak_output = response_text
                reprompt_text = get_localized_message('reprompt', locale)

            logger.info("Response generated successfully")
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt_text)
                    .response
            )

        except Exception as e:
            logger.error(f"Error in GptQueryIntentHandler: {str(e)}")
            logger.error(traceback.format_exc())
            locale = get_device_locale(handler_input)
            return (
                handler_input.response_builder
                    .speak(get_localized_message('error', locale))
                    .ask(get_localized_message('reprompt', locale))
                    .response
            )

class NextIntentHandler(AbstractRequestHandler):
    """Handler for hearing more follow-up suggestions."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.NextIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            session_attr = handler_input.attributes_manager.session_attributes
            locale = session_attr.get("device_locale", get_device_locale(handler_input))
            pending_followups = session_attr.get("pending_followups", [])

            if pending_followups and len(pending_followups) > 1:
                # Remove the first follow-up and present the next one
                pending_followups.pop(0)
                session_attr["pending_followups"] = pending_followups

                followup_text = get_localized_message('followup_intro', locale) + pending_followups[0] + get_localized_message('followup_outro', locale)
                speak_output = followup_text
            else:
                # No more follow-ups available
                speak_output = get_localized_message('reprompt', locale)

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(get_localized_message('reprompt', locale))
                    .response
            )
        except Exception as e:
            logger.error(f"Error in NextIntentHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Sorry, there was an error.")
                    .response
            )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            locale = get_device_locale(handler_input)
            if locale == 'ja':
                speak_output = "このスキルでは、どんな質問にもお答えします。例えば、「人工知能について教えて」や「物語を作って」などと聞いてみてください。"
            else:
                speak_output = "With this skill, you can ask me any question. Try asking 'What is artificial intelligence?' or 'Tell me a story about space'."

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(get_localized_message('reprompt', locale))
                    .response
            )
        except Exception as e:
            logger.error(f"Error in HelpIntentHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Sorry, there was an error.")
                    .response
            )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            locale = get_device_locale(handler_input)
            speak_output = get_localized_message('goodbye', locale)

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )
        except Exception as e:
            logger.error(f"Error in CancelOrStopIntentHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Goodbye!")
                    .response
            )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            logger.info(f"Session ended with reason: {handler_input.request_envelope.request.reason}")
            return handler_input.response_builder.response
        except Exception as e:
            logger.error(f"Error in SessionEndedRequestHandler: {str(e)}")
            return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            intent_name = ask_utils.get_intent_name(handler_input)
            speak_output = f"You just triggered {intent_name}"

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )
        except Exception as e:
            logger.error(f"Error in IntentReflectorHandler: {str(e)}")
            return (
                handler_input.response_builder
                    .speak("Sorry, there was an error.")
                    .response
            )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        logger.error(f"Error type: {type(exception).__name__}")
        logger.error(f"Error message: {str(exception)}")
        logger.error(traceback.format_exc())

        locale = get_device_locale(handler_input)
        speak_output = get_localized_message('error', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(get_localized_message('reprompt', locale))
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(NextIntentHandler())
sb.add_request_handler(ClearContextIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())  # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()