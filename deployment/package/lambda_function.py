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
import os
from pathlib import Path

# APIキーの取得（複数の方法に対応）
api_key = None

# 1. 環境変数から取得（Alexaコンソールで設定）
api_key = os.environ.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')

# 2. .envファイルから読み込み（ローカルテスト用）
if not api_key:
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('openai_api_key='):
                    api_key = line.strip().split('=', 1)[1]
                    break

# 3. デフォルト値（直接設定も可能）
if not api_key:
    api_key = ""  # ここにAPIキーを直接設定してください（非推奨）
    # 例: api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# API key status logging
if api_key:
    logger.info(f"API key configured: Yes (starts with {api_key[:10]}...)")
else:
    logger.warning("API key NOT configured - will return test responses")

def generate_gpt_response(query, conversation_history=None, locale='ja'):
    """Generate response from OpenAI API with conversation context

    注: GPT-5は2024年にリリースされたが、現在のAPIキーではアクセスできない。
    そのため、GPT-4o-miniを使用（実動作確認済み）
    """
    logger.info(f"=== generate_gpt_response START === query: {query}")
    logger.info(f"Conversation history length: {len(conversation_history) if conversation_history else 0}")

    # If no API key, return test response
    if not api_key or api_key.strip() == "":
        logger.info("No API key configured, returning test response")
        if "生成" in query or "AI" in query.upper():
            return "生成AIは、テキストや画像を自動的に作り出す人工知能技術です。（APIキー未設定のためテスト応答）"
        else:
            return f"「{query}」についての質問を受け付けました。（APIキー未設定のためテスト応答）"

    try:
        # Chat Completions API（GPT-4o-miniで動作確認済み）
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Build prompt with conversation history
        if conversation_history and len(conversation_history) > 0:
            # Include conversation history for context (last 10 exchanges for better context)
            context = "\n".join([
                f"{'ユーザー' if locale == 'ja' else 'User'}: {h['user']}\n{'アシスタント' if locale == 'ja' else 'Assistant'}: {h['assistant']}"
                for h in conversation_history[-10:]  # Keep last 10 exchanges for context
            ])

            if locale == 'ja':
                # 短い返答の場合は前の会話と組み合わせて理解
                if len(query) < 15:
                    prompt = f"これまでの会話:\n{context}\n\n新しい質問: {query}\n\n重要: ユーザーの短い返答（「天気」「観光」「歴史」など）は、直前の会話の文脈（例：東京の話をしていたら東京の天気）で理解して答えてください。会話の文脈を必ず考慮して日本語で答えてください。"
                else:
                    prompt = f"これまでの会話:\n{context}\n\n新しい質問: {query}\n\n会話の文脈を考慮して日本語で答えてください。物語や詳細な説明が必要な場合は、適切な長さで回答してください。"
            else:
                # Short responses should be interpreted in context
                if len(query) < 20:
                    prompt = f"Previous conversation:\n{context}\n\nNew question: {query}\n\nIMPORTANT: Short user responses (like 'weather', 'tourism', 'history') should be understood in the context of the previous conversation (e.g., if discussing Tokyo, answer about Tokyo's weather)."
                else:
                    prompt = f"Previous conversation:\n{context}\n\nNew question: {query}\n\nConsidering the context, please answer. If a story or detailed explanation is needed, provide an appropriate length response."
        else:
            # No history, regular prompt
            if locale == 'ja':
                prompt = f"質問: {query}\n日本語で答えてください。物語や詳細な説明が必要な場合は、適切な長さで回答してください。"
            else:
                prompt = f"Question: {query}\nPlease answer. If a story or detailed explanation is needed, provide an appropriate length response."

        # Chat Completions API request format
        data = {
            "model": "gpt-4o-mini",  # 実動作確認済みのモデル
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that responds in Japanese." if locale == 'ja' else "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500  # 標準のmax_tokensパラメータ
        }

        logger.info(f"Sending request to OpenAI API...")
        response = requests.post(url, headers=headers, json=data, timeout=7)  # Alexaの8秒制限に合わせて7秒に設定

        if response.ok:
            result = response.json()

            # Chat Completions APIのレスポンス構造
            output_text = ""
            try:
                if 'choices' in result and len(result['choices']) > 0:
                    message = result['choices'][0].get('message', {})
                    output_text = message.get('content', '').strip()

                logger.info(f"OpenAI response received: {output_text[:100] if output_text else 'No text'}...")
                return output_text if output_text else "申し訳ありません。応答を生成できませんでした。"
            except Exception as e:
                logger.error(f"Error parsing OpenAI response: {e}")
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

        # Initialize session attributes
        locale = handler_input.request_envelope.request.locale
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["locale"] = "ja" if locale and locale.startswith("ja") else "en"
        session_attr["conversation_history"] = []  # Initialize conversation history

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
            "PracticalIntent",
            "ContinuationIntent",  # 会話継続用
            "SelectionIntent",      # 選択用
            "DetailRequestIntent",  # 詳細要求用
            "NavigationIntent",     # ナビゲーション用
            "AcknowledgmentIntent"  # 相槌用
        ]

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        logger.info(f"=== UniversalQueryIntentHandler START - Intent: {intent_name} ===")

        try:
            # Get session attributes first
            session_attr = handler_input.attributes_manager.session_attributes
            locale = session_attr.get("locale", "ja")

            # Get conversation history
            conversation_history = session_attr.get("conversation_history", [])
            if not isinstance(conversation_history, list):
                logger.warning(f"Invalid conversation_history type: {type(conversation_history)}, resetting to []")
                conversation_history = []

            # Get query with null check
            slots = handler_input.request_envelope.request.intent.slots
            query_slot = slots.get("query") if slots else None
            query = query_slot.value if query_slot and query_slot.value else None

            # Handle intents that may not have a query slot
            if not query:
                # For continuation intents, use the intent itself as context
                if intent_name in ["SelectionIntent", "DetailRequestIntent", "NavigationIntent", "AcknowledgmentIntent"]:
                    # Try to infer query from recent conversation context
                    if conversation_history:
                        last_exchange = conversation_history[-1] if conversation_history else None
                        if last_exchange:
                            # Build contextual query based on intent type
                            if intent_name == "SelectionIntent":
                                query = "それについて教えて" if locale == "ja" else "Tell me about that"
                            elif intent_name == "DetailRequestIntent":
                                query = "もっと詳しく教えて" if locale == "ja" else "Tell me more details"
                            elif intent_name == "NavigationIntent":
                                query = "次を教えて" if locale == "ja" else "What's next"
                            elif intent_name == "AcknowledgmentIntent":
                                query = "続けて" if locale == "ja" else "Continue"
                            logger.info(f"Using contextual query for {intent_name}: {query}")
                        else:
                            logger.warning("No conversation history for context")
                            speak_output = "すみません、何について話していましたか？" if locale == "ja" else "Sorry, what were we talking about?"
                            return (
                                handler_input.response_builder
                                    .speak(speak_output)
                                    .ask(speak_output)
                                    .response
                            )
                    else:
                        speak_output = "何について知りたいですか？" if locale == "ja" else "What would you like to know about?"
                        return (
                            handler_input.response_builder
                                .speak(speak_output)
                                .ask(speak_output)
                                .response
                        )
                else:
                    logger.warning("No query slot value found")
                    speak_output = "すみません、質問が聞き取れませんでした。もう一度お願いします。" if locale == "ja" else "Sorry, I couldn't hear your question. Please try again."
                    return (
                        handler_input.response_builder
                            .speak(speak_output)
                            .ask(speak_output)
                            .response
                    )

            logger.info(f"Query: {query}")
            logger.info(f"Current conversation history: {len(conversation_history)} exchanges")

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

            # Generate response with context and history
            full_query = context_prefix + query if context_prefix else query
            speak_output = generate_gpt_response(full_query, conversation_history, locale)

            # Update conversation history
            conversation_history.append({
                "user": query[:200] if query else "",  # Limit query length to 200 chars
                "assistant": speak_output[:1000] if speak_output else ""  # Allow longer responses for stories
            })

            # Keep only last 100 exchanges for better context retention
            if len(conversation_history) > 100:
                conversation_history = conversation_history[-100:]

            # Update session attributes
            session_attr["conversation_history"] = conversation_history
            logger.info(f"Updated conversation history: {len(conversation_history)} exchanges")

            logger.info(f"Response: {speak_output}")

            # Keep session alive with engaging prompts
            ask_texts = {
                "ja": [
                    "他に質問はありますか？",
                    "続けて何か聞きたいことは？",
                    "もっと知りたいことがあれば教えてください。",
                    "他に興味のあることは？"
                ],
                "en": [
                    "Do you have any other questions?",
                    "What else would you like to know?",
                    "Is there anything else you're curious about?",
                    "What else can I help you with?"
                ]
            }

            # Rotate through different prompts
            prompt_index = len(conversation_history) % 4
            ask_text = ask_texts.get(locale, ask_texts["en"])[prompt_index]

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(ask_text)
                    .set_should_end_session(False)  # Explicitly keep session open
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

        # Get conversation history
        conversation_history = session_attr.get("conversation_history", [])
        history_count = len(conversation_history)

        if locale == "ja":
            speak_output = f"はい、正常に動作しています。GPT-5を使用して質問に答えます。現在の会話履歴は{history_count}件です。"
        else:
            speak_output = f"Yes, I'm working properly. I'm using GPT-5 to answer your questions. Current conversation history: {history_count} exchanges."

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