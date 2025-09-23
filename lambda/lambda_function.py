# -*- coding: utf-8 -*-

import os
import re
import json
import logging
import requests
from pathlib import Path

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor
)
import ask_sdk_core.utils as ask_utils

# -------------------------------------------------
# ログ初期化（必ず最初に実行）
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    force=True
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)
print("### MODULE LOADED")

# ===========================================
# APIキー設定（3通りの併用）
# ===========================================
OPENAI_API_KEY_DIRECT = ""  # ← 直書きは開発のみ推奨（本番は環境変数）
api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("openai_api_key")

if OPENAI_API_KEY_DIRECT and OPENAI_API_KEY_DIRECT.strip():
    api_key = OPENAI_API_KEY_DIRECT.strip()
    logger.info("Using directly configured API key")

if not api_key:
    try:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k in ["OPENAI_API_KEY", "openai_api_key"]:
                        api_key = v.strip(" '\"\t")
                        logger.info("API key loaded from .env file")
                        break
    except Exception as e:
        logger.error(f".env load error: {e}")

api_key = (api_key or "").strip()
if api_key:
    logger.info("API key configured (starts with %s...)", api_key[:10])
else:
    logger.warning("API key NOT configured - will return test/fallback responses")

# ===========================================
# ユーティリティ
# ===========================================
def safe_json(obj, maxlen=800):
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        return s if len(s) <= maxlen else s[:maxlen] + f"...(truncated {len(s)-maxlen} chars)"
    except Exception as e:
        return f"<json-dump-error: {e}>"

def strip_markdown(text: str) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"`{1,3}([^`]*)`{1,3}", r"\1", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"_([^_]+)_", r"\1", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def to_ssml_safe(text: str, max_chars: int = 400) -> str:
    text = (text or "すみません、うまく答えを取得できませんでした。")[:max_chars]
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<speak>{text}</speak>"

def get_slot_value(handler_input, slot_name: str) -> str:
    """Slot 安全取得（存在しない・空でもエラーにしない）"""
    intent = getattr(handler_input.request_envelope.request, "intent", None)
    slots = getattr(intent, "slots", {}) or {}
    slot = slots.get(slot_name)
    return getattr(slot, "value", "") if slot else ""

# ===========================================
# OpenAI 呼び出し（Responses API）
# ===========================================
OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"
OPENAI_MODEL = "gpt-5-mini"   # 要件に合わせて調整可

def generate_gpt_response(query, conversation_history=None, locale='ja'):
    logger.info("=== generate_gpt_response START === query=%s", query)
    logger.info("Conversation history len=%s", len(conversation_history) if conversation_history else 0)

    # APIキー未設定ならフォールバック
    if not api_key:
        test_responses = {
            "こんにちは": "こんにちは！テストモードです。APIキーを設定してください。",
            "生成AI": "生成AIはデータから新しいコンテンツを作る技術です。（テスト）",
            "天気": "天気は外部API連携後に対応予定です。（テスト）",
        }
        for k, v in test_responses.items():
            if k in (query or ""):
                return v
        return f"「{query}」ですね。現在はテストモードのため、ダミー回答です。"

    # 履歴を使ったプロンプト
    if conversation_history:
        ctx = "\n".join([f"ユーザー: {h['user']}\nアシスタント: {h['assistant']}" for h in conversation_history[-10:]])
        if locale.startswith("ja"):
            if query and len(query) < 15:
                prompt = f"これまでの会話:\n{ctx}\n\n新しい質問: {query}\n短い質問は直前の文脈を踏まえて日本語で簡潔に答えてください。"
            else:
                prompt = f"これまでの会話:\n{ctx}\n\n新しい質問: {query}\n文脈を踏まえ、日本語で適切な長さで答えてください。"
        else:
            prompt = f"Previous conversation:\n{ctx}\n\nNew question: {query}\nAnswer concisely using context."
    else:
        prompt = f"質問: {query}\n日本語で、60文字以内で簡潔に答えてください。" if locale.startswith("ja") \
                 else f"Question: {query}\nAnswer concisely in 60 words or less."

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": OPENAI_MODEL,
        "input": prompt,
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "low"}
    }

    try:
        logger.info("Calling OpenAI: model=%s", OPENAI_MODEL)
        r = requests.post(OPENAI_ENDPOINT, headers=headers, json=body, timeout=6.0)  # 体感と成功率のバランス
        r.raise_for_status()
        j = r.json()

        out = j.get("output_text", "")
        if not out and isinstance(j.get("output"), list) and len(j["output"]) > 1:
            msg = j["output"][1]
            if isinstance(msg, dict) and "content" in msg and msg["content"]:
                c0 = msg["content"][0]
                if isinstance(c0, dict):
                    out = c0.get("text", "") or out

        out = strip_markdown(out)
        if not out:
            out = "すみません、うまく答えを取得できませんでした。"
        logger.info("OpenAI OK: %s", out[:120])
        return out

    except requests.exceptions.Timeout:
        logger.error("OpenAI timeout")
        return "少し時間がかかっています。もう一度お試しください。"
    except Exception as e:
        logger.error("OpenAI error: %s", e, exc_info=True)
        return "応答の取得中にエラーが発生しました。時間をおいてお試しください。"

# ===========================================
# インターセプタ（毎回ログ）
# ===========================================
class LoggingRequestInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        try:
            rtype = ask_utils.request_util.get_request_type(handler_input)
        except Exception:
            rtype = "Unknown"
        logger.info(">>> [REQ] type=%s", rtype)
        try:
            env = handler_input.request_envelope
            summary = {
                "type": getattr(env.request, "object_type", None),
                "locale": getattr(env.request, "locale", None),
                "intent": getattr(getattr(env.request, "intent", None), "name", None),
                "userId": getattr(getattr(env.context, "system", None), "user", None)
                          and getattr(env.context.system.user, "user_id", None)
            }
            logger.info(">>> [REQ-SUM] %s", safe_json(summary))
        except Exception as e:
            logger.warning("REQ summary failed: %s", e)

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        try:
            speak = getattr(getattr(response, "output_speech", None), "text", None) or \
                    getattr(getattr(response, "output_speech", None), "ssml", None)
            end = getattr(response, "should_end_session", None)
            logger.info("<<< [RES] end=%s speak=%s", end, (speak[:80] + "..." if speak and len(speak) > 80 else speak))
        except Exception as e:
            logger.warning("RES summary failed: %s", e)

# ===========================================
# Handlers
# ===========================================
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("=== LaunchRequest ===")
        session = handler_input.attributes_manager.session_attributes
        session["conversation_history"] = []
        session["locale"] = getattr(handler_input.request_envelope.request, "locale", "ja-JP")

        speak = "じぇないアシスタントへようこそ。質問をどうぞ。" if api_key \
                else "じぇないアシスタントへようこそ。OpenAI の APIキーが未設定です。環境変数 OPENAI_API_KEY を設定してください。"
        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("何についてお答えしますか？")).response

class GptQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== GptQueryIntent ===")
        query = get_slot_value(handler_input, "query")
        logger.info("Query=%s", query if query else "<empty>")

        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        locale = session.get("locale", "ja-JP")

        if not query:
            speak = "質問が聞き取れませんでした。もう一度お願いします。"
        else:
            speak = generate_gpt_response(query, history, locale)
            history.append({"user": query, "assistant": speak})
            if len(history) > 100:
                history = history[-100:]
            session["conversation_history"] = history

        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("他に質問はありますか？")).response

class ContinuationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ContinuationIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== ContinuationIntent ===")
        continuation = get_slot_value(handler_input, "continuation")
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        locale = session.get("locale", "ja-JP")

        if not continuation:
            speak = "どの点を詳しく知りたいですか？"
        else:
            speak = generate_gpt_response(continuation, history, locale)
            history.append({"user": continuation, "assistant": speak})
            session["conversation_history"] = history[-100:]

        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("他に質問はありますか？")).response

class ContextContinuationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ContextContinuationIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== ContextContinuationIntent ===")
        aspect = get_slot_value(handler_input, "aspect")
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        locale = session.get("locale", "ja-JP")

        if not aspect:
            speak = "どの点について詳しく知りたいですか？"
        else:
            speak = generate_gpt_response(aspect, history, locale)
            history.append({"user": aspect, "assistant": speak})
            session["conversation_history"] = history[-100:]

        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("他に知りたいことはありますか？")).response

class TopicChangeIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("TopicChangeIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== TopicChangeIntent ===")
        new_topic = get_slot_value(handler_input, "newTopic")
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        locale = session.get("locale", "ja-JP")

        if not new_topic:
            speak = "何について話しましょうか？"
        else:
            speak = generate_gpt_response(new_topic, history, locale)
            history.append({"user": new_topic, "assistant": speak})
            session["conversation_history"] = history[-100:]

        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("この話題について他に質問はありますか？")).response

# ★ 追加: DetailRequestIntent（以前エラーが出たインテント）
class DetailRequestIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DetailRequestIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("=== DetailRequestIntent ===")
        query = get_slot_value(handler_input, "query") or "詳細を教えて"
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        locale = session.get("locale", "ja-JP")

        speak = generate_gpt_response(query, history, locale)
        history.append({"user": query, "assistant": speak})
        session["conversation_history"] = history[-100:]
        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("他に質問はありますか？")).response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak = "じぇないアシスタントは、質問に簡潔にお答えします。例えば『東京の気温は？』などと聞いてください。"
        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("何を知りたいですか？")).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or \
               ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        speak = "さようなら。"
        return handler_input.response_builder.speak(to_ssml_safe(speak)).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("Session ended: %s", getattr(handler_input.request_envelope.request, "reason", None))
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error("=== EXCEPTION CAUGHT ===", exc_info=True)
        speak = f"予期しないエラーです。{str(exception)[:30]}"
        return handler_input.response_builder.speak(to_ssml_safe(speak)).ask(to_ssml_safe("もう一度お試しください。")).response

# ===========================================
# Skill 構築
# ===========================================
sb = SkillBuilder()
# 具体的 → 汎用 の順で登録
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(ContinuationIntentHandler())
sb.add_request_handler(ContextContinuationIntentHandler())
sb.add_request_handler(TopicChangeIntentHandler())
sb.add_request_handler(DetailRequestIntentHandler())  # ★ 追加
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())
sb.add_global_request_interceptor(LoggingRequestInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()
