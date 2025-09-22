"""
Alexa GenAI Assistant Lambda Function
GPT-5 API integration with improved error handling
"""

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import requests
import logging
import json

# Set your OpenAI API key
api_key = ""  # ここにAPIキーを直接設定してください
# 例: api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# GPT-5 model
model = "gpt-5-mini"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_gpt_response(query, locale='ja'):
    """Generate response from GPT-5 API"""
    logger.info(f"=== generate_gpt_response START === query: {query}")

    # If no API key, return test response
    if not api_key or api_key.strip() == "":
        logger.info("No API key configured, returning test response")
        if "生成" in query or "AI" in query.upper():
            return "生成AIは、テキストや画像を自動的に作り出す人工知能技術です。（APIキー未設定のためテスト応答）"
        else:
            return f"「{query}」についての質問を受け付けました。（APIキー未設定のためテスト応答）"

    try:
        # GPT-5 Responses API
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create prompt
        if locale == 'ja':
            prompt = f"質問: {query}\n回答を50文字以内で簡潔に日本語で答えてください。"
        else:
            prompt = f"Question: {query}\nAnswer briefly in 50 words or less."

        # GPT-5 request format
        data = {
            "model": model,
            "input": prompt,
            "reasoning": {
                "effort": "low"  # Use low effort for quick responses
            },
            "text": {
                "verbosity": "low"  # Concise responses
            }
        }

        logger.info(f"Sending request to GPT-5...")
        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.ok:
            result = response.json()

            # GPT-5のレスポンス構造に対応
            # output[1].content[0].text に実際のテキストがある
            output_text = ""
            try:
                if 'output' in result and len(result['output']) > 1:
                    message = result['output'][1]  # 2番目の要素がメッセージ
                    if 'content' in message and len(message['content']) > 0:
                        output_text = message['content'][0].get('text', '')

                # 旧形式のフォールバック
                if not output_text:
                    output_text = result.get('output_text', '')

                logger.info(f"GPT-5 response received: {output_text[:100] if output_text else 'No text'}...")
                return output_text if output_text else "申し訳ありません。応答を生成できませんでした。"
            except Exception as e:
                logger.error(f"Error parsing GPT-5 response: {e}")
                logger.error(f"Response structure: {json.dumps(result, ensure_ascii=False)[:500]}")
                return "応答の解析中にエラーが発生しました。"
        else:
            logger.error(f"API Error {response.status_code}: {response.text}")
            return f"APIエラーが発生しました。（エラーコード: {response.status_code}）"

    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return "応答に時間がかかりすぎました。もう一度お試しください。"
    except Exception as e:
        logger.error(f"Error in generate_gpt_response: {str(e)}", exc_info=True)
        return "エラーが発生しました。もう一度お試しください。"

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("=== LaunchRequestHandler START ===")

        # Store locale
        locale = handler_input.request_envelope.request.locale
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["locale"] = "ja" if locale and locale.startswith("ja") else "en"

        speak_output = "じぇないアシスタントへようこそ。何かお手伝いしましょうか？" if session_attr["locale"] == "ja" else "Welcome to Gen AI Assistant. How can I help you?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class UniversalQueryIntentHandler(AbstractRequestHandler):
    """Handle all query intents with the same logic"""
    def can_handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        # Handle all custom intents that have a query slot
        return intent_name in [
            "GptQueryIntent",
            "CreativeIntent",
            "EntertainmentIntent",
            "EmotionalIntent",
            "AnalysisIntent",
            "HelpIntent",
            "PhilosophicalIntent",
            "PracticalIntent"
        ]

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        logger.info(f"=== UniversalQueryIntentHandler START - Intent: {intent_name} ===")

        try:
            # Get query
            query = handler_input.request_envelope.request.intent.slots["query"].value
            logger.info(f"Query: {query}")

            # Get locale
            session_attr = handler_input.attributes_manager.session_attributes
            locale = session_attr.get("locale", "ja")

            # Add context based on intent type
            context_prefix = ""
            if intent_name == "CreativeIntent":
                context_prefix = "創作的に答えて: " if locale == "ja" else "Be creative: "
            elif intent_name == "EntertainmentIntent":
                context_prefix = "楽しく答えて: " if locale == "ja" else "Be entertaining: "
            elif intent_name == "EmotionalIntent":
                context_prefix = "感情的に答えて: " if locale == "ja" else "Be emotional: "
            elif intent_name == "AnalysisIntent":
                context_prefix = "分析的に答えて: " if locale == "ja" else "Be analytical: "
            elif intent_name == "PhilosophicalIntent":
                context_prefix = "哲学的に答えて: " if locale == "ja" else "Be philosophical: "
            elif intent_name == "PracticalIntent":
                context_prefix = "実践的に答えて: " if locale == "ja" else "Be practical: "

            # Generate response with context
            full_query = context_prefix + query if context_prefix else query
            speak_output = generate_gpt_response(full_query, locale)

            logger.info(f"Response: {speak_output}")

            ask_text = "他に質問はありますか？" if locale == "ja" else "Do you have any other questions?"

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(ask_text)
                    .response
            )

        except Exception as e:
            logger.error(f"ERROR in UniversalQueryIntentHandler: {str(e)}", exc_info=True)
            locale = handler_input.attributes_manager.session_attributes.get("locale", "ja")
            speak_output = "エラーが発生しました。もう一度お試しください。" if locale == "ja" else "An error occurred. Please try again."
            ask_text = "他に質問はありますか？" if locale == "ja" else "Do you have any other questions?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(ask_text)
                    .response
            )

class TestIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("TestIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== TestIntentHandler START ===")

        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("locale", "ja")

        if locale == "ja":
            speak_output = "はい、正常に動作しています。GPT-5を使用して質問に答えます。"
        else:
            speak_output = "Yes, I'm working properly. I'm using GPT-5 to answer your questions."

        ask_text = "何か質問はありますか？" if locale == "ja" else "What would you like to ask?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(ask_text)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("locale", "ja")

        if locale == "ja":
            speak_output = "何でも質問してください。例えば、「生成AIとは何か」と聞いてみてください。"
        else:
            speak_output = "You can ask me anything. For example, try asking 'What is generative AI?'"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== FallbackIntentHandler TRIGGERED ===")

        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("locale", "ja")

        if locale == "ja":
            speak_output = "すみません、よく分かりませんでした。もう一度お願いします。"
        else:
            speak_output = "Sorry, I didn't understand that. Could you please repeat?"

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
        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("locale", "ja")

        speak_output = "さようなら" if locale == "ja" else "Goodbye!"

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

        session_attr = handler_input.attributes_manager.session_attributes
        locale = session_attr.get("locale", "ja")

        if locale == "ja":
            speak_output = "予期しないエラーが発生しました。もう一度お試しください。"
            ask_output = "他に何かお手伝いしましょうか？"
        else:
            speak_output = "An unexpected error occurred. Please try again."
            ask_output = "How else can I help you?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(ask_output)
                .response
        )

# Build skill
sb = SkillBuilder()

# Add request handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(UniversalQueryIntentHandler())
sb.add_request_handler(TestIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Add exception handler
sb.add_exception_handler(CatchAllExceptionHandler())

# Lambda handler
lambda_handler = sb.lambda_handler()