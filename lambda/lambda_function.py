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
api_key = ""  # ここにAPIキーを直接設定してください

# GPT-5 model - choose from gpt-5, gpt-5-mini, or gpt-5-nano
# gpt-5: Best performance ($1.25/1M input, $10/1M output)
# gpt-5-mini: Balanced ($0.25/1M input, $2/1M output)
# gpt-5-nano: Most economical ($0.05/1M input, $0.40/1M output)
model = "gpt-5-mini"  # Using gpt-5-mini for balanced performance and cost

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
            'help': "You can ask me any question and I'll try to help. Just say something like 'tell me about artificial intelligence' or 'what is the weather like today'. What would you like to know?",
            'error': "Sorry, I had trouble doing what you asked. Please try again.",
            'reprompt': "You can ask me another question or say stop to end the conversation.",
            'reprompt_with_followup': "You can ask me another question, say 'next' to hear more suggestions, or say stop to end the conversation.",
            'followup_intro': "You could ask: ",
            'followup_outro': ". What would you like to know?",
            'clear_context': "I've cleared our conversation history. What would you like to talk about?",
            'default_followup_1': "Tell me more",
            'default_followup_2': "Give me an example",
            'test': "Hello! Gen AI is working properly. You can ask me any question."
        },
        'ja': {
            'welcome': "じぇないアシスタントへようこそ。何かお手伝いしましょうか？",
            'goodbye': "じぇないアシスタントをご利用いただきありがとうございました。さようなら！",
            'help': "何でも質問してください。たとえば「人工知能について教えて」や「今日の天気は」と言ってみてください。何か知りたいことはありますか？",
            'error': "申し訳ございません。エラーが発生しました。もう一度お試しください。",
            'reprompt': "他に質問がありましたらどうぞ。終了する場合は「ストップ」と言ってください。",
            'reprompt_with_followup': "他に質問がありましたらどうぞ。提案を聞く場合は「次」、終了する場合は「ストップ」と言ってください。",
            'followup_intro': "こんな質問はいかがですか: ",
            'followup_outro': "。何か知りたいことはありますか？",
            'clear_context': "会話履歴をクリアしました。何についてお話ししましょうか？",
            'default_followup_1': "詳しく教えて",
            'default_followup_2': "例を教えて",
            'test': "こんにちは！じぇないは正常に動作しています。何でも質問してください。"
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
            logger.info("LaunchRequestHandler called")
            locale = get_device_locale(handler_input)
            logger.info(f"Detected locale: {locale}")

            speak_output = get_localized_message('welcome', locale)
            logger.info(f"Welcome message: {speak_output}")

            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["chat_history"] = []
            session_attr["device_locale"] = locale

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        except Exception as e:
            logger.error(f"Error in LaunchRequestHandler: {str(e)}", exc_info=True)
            raise

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value

        session_attr = handler_input.attributes_manager.session_attributes

        # Get or detect language
        device_locale = session_attr.get("device_locale", get_device_locale(handler_input))
        query_lang = detect_language(query)

        # Use query language if Japanese is detected, otherwise use device locale
        locale = query_lang if query_lang == 'ja' else device_locale
        session_attr["current_locale"] = locale

        if "chat_history" not in session_attr:
            session_attr["chat_history"] = []
            session_attr["last_context"] = None

        # Process the query to determine if it's a follow-up question
        processed_query, is_followup = process_followup_question(query, session_attr.get("last_context"), locale)

        # Generate response with enhanced context handling
        response_data = generate_gpt_response(session_attr["chat_history"], processed_query, is_followup, locale)

        # Handle the response data which could be a tuple or string
        if isinstance(response_data, tuple) and len(response_data) == 2:
            response_text, followup_questions = response_data
        else:
            # Fallback for error cases
            response_text = str(response_data)
            followup_questions = []

        # Store follow-up questions in the session
        session_attr["followup_questions"] = followup_questions

        # Update the conversation history with just the response text, not the questions
        session_attr["chat_history"].append((query, response_text))
        session_attr["last_context"] = extract_context(query, response_text)

        # Format the response with follow-up suggestions if available
        response = response_text
        if followup_questions and len(followup_questions) > 0:
            # Add a short pause before the suggestions
            response += " <break time=\"0.5s\"/> "
            response += get_localized_message('followup_intro', locale)
            # Join with appropriate connector based on language
            connector = "、" if locale == 'ja' else ", "
            last_connector = "、または" if locale == 'ja' else ", or "

            if len(followup_questions) > 1:
                response += connector.join([f"「{q}」" if locale == 'ja' else f"'{q}'" for q in followup_questions[:-1]])
                response += f"{last_connector}「{followup_questions[-1]}」" if locale == 'ja' else f"{last_connector}'{followup_questions[-1]}'"
            else:
                response += f"「{followup_questions[0]}」" if locale == 'ja' else f"'{followup_questions[0]}'"
            response += get_localized_message('followup_outro', locale)

        # Prepare response with reprompt
        reprompt_key = 'reprompt_with_followup' if followup_questions else 'reprompt'
        reprompt_text = get_localized_message(reprompt_key, locale)

        return (
            handler_input.response_builder
                .speak(response)
                .ask(reprompt_text)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(f"Error caught: {str(exception)}", exc_info=True)
        logger.error(f"Exception type: {type(exception).__name__}")
        logger.error(f"Request type: {handler_input.request_envelope.request.object_type}")

        # エラーの詳細をログに記録
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("current_locale", get_device_locale(handler_input))

        # デバッグ用により詳細なエラーメッセージを返す（本番では削除）
        error_detail = str(exception)[:100] if exception else "Unknown error"
        speak_output = f"{get_localized_message('error', locale)} Debug: {error_detail}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(get_localized_message('error', locale))
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
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("current_locale", get_device_locale(handler_input))
        speak_output = get_localized_message('goodbye', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

def process_followup_question(question, last_context, locale='en'):
    """Processes a question to determine if it's a follow-up and enhances it with context if needed"""
    # Common follow-up indicators for English
    en_followup_patterns = [
        r'^(what|how|why|when|where|who|which)\s+(about|is|are|was|were|do|does|did|can|could|would|should|will)\s',
        r'^(and|but|so|then|also)\s',
        r'^(can|could|would|should|will)\s+(you|it|they|we)\s',
        r'^(is|are|was|were|do|does|did)\s+(it|that|this|they|those|these)\s',
        r'^(tell me more|elaborate|explain further)\s*',
        r'^(why|how)\?*$'
    ]

    # Common follow-up indicators for Japanese
    ja_followup_patterns = [
        r'(それ|これ|あれ)(は|って|の)',
        r'^(でも|そして|また|あと|それから)',
        r'(について|に関して|のこと)',
        r'^(なぜ|どうして|どう|どのように)',
        r'(もっと|詳しく|具体的に)',
        r'(例えば|たとえば|例を)'
    ]

    followup_patterns = ja_followup_patterns if locale == 'ja' else en_followup_patterns
    is_followup = False

    # Check if the question matches any follow-up patterns
    for pattern in followup_patterns:
        if re.search(pattern, question.lower() if locale == 'en' else question):
            is_followup = True
            break

    return question, is_followup

def extract_context(question, response):
    """Extracts the main context from a Q&A pair for future reference"""
    return {"question": question, "response": response}

def generate_followup_questions(conversation_context, query, response, locale='en', count=2):
    """Generates concise follow-up questions based on the conversation context"""
    try:
        if not api_key:
            logger.warning("API key not configured, using default follow-ups")
            return [get_localized_message('default_followup_1', locale),
                   get_localized_message('default_followup_2', locale)]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        url = "https://api.openai.com/v1/chat/completions"

        # Prepare prompt based on language
        if locale == 'ja':
            system_content = "あなたは短いフォローアップ質問を提案する日本語アシスタントです。"
            user_content = """会話に基づいて、とても短いフォローアップ質問を2つ提案してください（各5文字以内）。
            シンプルで直接的にしてください。質問のみを'|'で区切って返してください。
            例: 理由は？|具体例は？"""
        else:
            system_content = "You are a helpful assistant that suggests short follow-up questions."
            user_content = """Based on the conversation, suggest 2 very short follow-up questions (max 4 words each).
            Make them direct and simple. Return ONLY the questions separated by '|'.
            Example: What's the capital?|How big is it?"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        # Add conversation context
        if conversation_context:
            last_q, last_a = conversation_context[-1]
            q_prefix = "前の質問: " if locale == 'ja' else "Previous Q: "
            messages.append({"role": "user", "content": f"{q_prefix}{last_q}"})
            messages.append({"role": "assistant", "content": last_a})

        q_current = "現在の質問: " if locale == 'ja' else "Current Q: "
        q_prompt = "フォローアップ質問（|で区切る）:" if locale == 'ja' else "Follow-up questions (separated by |):"

        messages.append({"role": "user", "content": f"{q_current}{query}"})
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": q_prompt})

        data = {
            "model": "gpt-5-nano",  # Using lightweight model for quick follow-up generation
            "messages": messages,
            "max_tokens": 50,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=3)
        if response.ok:
            questions_text = response.json()['choices'][0]['message']['content'].strip()
            # Clean and split the response
            questions = [q.strip().rstrip('?？') for q in questions_text.split('|') if q.strip()]

            # Validate questions based on language
            if locale == 'ja':
                questions = [q for q in questions if len(q) <= 10 and len(q) > 0][:2]
            else:
                questions = [q for q in questions if len(q.split()) <= 4 and len(q) > 0][:2]

            # If we don't have enough questions, provide defaults
            if len(questions) < 2:
                questions = [get_localized_message('default_followup_1', locale),
                           get_localized_message('default_followup_2', locale)]

            logger.info(f"Generated follow-up questions ({locale}): {questions}")
            return questions

        logger.error(f"API Error: {response.text}")
        return [get_localized_message('default_followup_1', locale),
                get_localized_message('default_followup_2', locale)]

    except Exception as e:
        logger.error(f"Error in generate_followup_questions: {str(e)}")
        return [get_localized_message('default_followup_1', locale),
                get_localized_message('default_followup_2', locale)]

def generate_gpt_response(chat_history, new_question, is_followup=False, locale='en'):
    """Generates a GPT response to a question with enhanced context handling"""
    if not api_key:
        error_msg = "API key not configured. Please set your OpenAI API key in the Lambda function." if locale == 'en' else "APIキーが設定されていません。Lambda関数にOpenAI APIキーを設定してください。"
        logger.error("OpenAI API key not configured")
        return error_msg, []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/chat/completions"

    # Create system message based on language and context
    if locale == 'ja':
        system_message = "あなたは親切なアシスタントです。50文字以内で簡潔に答えてください。"
        if is_followup:
            system_message += " これは前の会話のフォローアップ質問です。すでに提供した情報を繰り返さず、文脈を維持してください。"
    else:
        system_message = "You are a helpful assistant. Answer in 50 words or less."
        if is_followup:
            system_message += " This is a follow-up question to the previous conversation. Maintain context without repeating information already provided."

    # Enhanced system message for GPT-5's advanced capabilities
    messages = [{"role": "system", "content": system_message}]

    # Include relevant conversation history
    history_limit = 10 if not is_followup else 5
    for question, answer in chat_history[-history_limit:]:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})

    # Add the new question
    messages.append({"role": "user", "content": new_question})

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7,  # Balanced creativity and accuracy
        "reasoning_effort": "medium"  # GPT-5 specific parameter for balanced reasoning
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        if response.ok:
            response_text = response_data['choices'][0]['message']['content']

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
            return f"Error {response.status_code}: {response_data['error']['message']}", []
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}", []

class ClearContextIntentHandler(AbstractRequestHandler):
    """Handler for clearing conversation context."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ClearContextIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
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

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("device_locale", get_device_locale(handler_input))
        speak_output = get_localized_message('help', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("device_locale", get_device_locale(handler_input))

        # セッションが新しい場合は起動メッセージを返す（一時的な対処）
        if handler_input.request_envelope.session.new:
            logger.info("New session detected in FallbackIntent - treating as launch")
            speak_output = get_localized_message('welcome', locale)
            session_attr["chat_history"] = []
            session_attr["device_locale"] = locale
        else:
            speak_output = get_localized_message('error', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class TestIntentHandler(AbstractRequestHandler):
    """Handler for Test Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TestIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("device_locale", get_device_locale(handler_input))
        speak_output = get_localized_message('test', locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # Any cleanup logic goes here.
        logger.info("Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))

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
        intent_name = ask_utils.get_intent_name(handler_input)
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("device_locale", get_device_locale(handler_input))

        if locale == 'ja':
            speak_output = f"「{intent_name}」というインテントをトリガーしました。"
        else:
            speak_output = f"You just triggered {intent_name} intent."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

sb = SkillBuilder()

# Register handlers in specific order - most specific first
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(TestIntentHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(ClearContextIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())  # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()