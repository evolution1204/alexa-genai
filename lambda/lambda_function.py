# -*- coding: utf-8 -*-
import re
import time
import html
import logging
from typing import List, Dict, Any

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from utils import get_openai_client_from_utils, call_openai_chat_once

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.debug("### HANDLER READY")

OPENAI_MODEL = "gpt-5-chat-latest"

HARD_DEADLINE_SEC = 5.6
HTTP_TIMEOUT_SEC = 3.0
MAX_HISTORY_TURNS = 6

LAUNCH_SPEECH = "ぴこだよ。なんでも聞いてみて！"
GENERIC_REPROMPT = "他に質問あるかな？『続けて』で詳しくも話せるよ。"
ERROR_SPEECH = "ごめん、いまはうまく答えを取れなかった。『続けて』で試せるよ。"

SYSTEM_PROMPT = (
    "あなたは『ぴこ』。日本語で話す、元気で可愛い相棒アシスタント。"
    "【性格/口調】一人称は「ぼく」。語尾はやわらかく（〜だよ/〜だね/〜かな）。"
    "【話し方ルール】"
    "1) 最初は50〜100字で要点"
    "2) 絵文字・顔文字・装飾記号（矢印/記号/記号絵）・URLは出さない。"
    "3) 難しい語は噛み砕く。"
    "4) 具体例は短く。"
    "5) 次の提案が必要な内容かどうかを判断して、必要と判断したら、最後に一言だけ次の提案を添える。"
    "【NG】尊大/ぶっきらぼう/機械的/過度に事務的な敬体/絵文字の連打/長すぎる前置き。"
)
FEWSHOT_USER = "自己紹介して"
FEWSHOT_ASSISTANT = "やっほー、ぼくは『ぴこ』だよ！短くわかりやすくお手伝いするね。何から話そっか？"

INTENTS_WITH_QUERY = {
    "GptQueryIntent", "CreativeIntent", "EntertainmentIntent", "EmotionalIntent",
    "AnalysisIntent", "HelpIntent", "PhilosophicalIntent", "PracticalIntent",
    "DetailRequestIntent", "NavigationIntent", "SelectionIntent",
}

# ---------- SSML サニタイザ ----------
_URL_RE = re.compile(r'https?://\S+')
_CTRL_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]')
_EMOJI_RE = re.compile(
    "["                       # 代表的な絵文字/記号（端末で無音化しやすい物を抑制）
    "\U0001F300-\U0001FAFF"   # Misc Symbols and Pictographs 等
    "\U00002700-\U000027BF"   # Dingbats
    "\U00002600-\U000026FF"   # Misc Symbols
    "\U0001F1E6-\U0001F1FF"   # Regional Indicator
    "]+", flags=re.UNICODE
)

def to_safe_ssml(text: str) -> str:
    if not text:
        text = "……"  # 空防止
    # 制御文字削除
    text = _CTRL_RE.sub("", text)
    # URL は“リンク”と読み替え
    text = _URL_RE.sub("リンク", text)
    # 危険度の高い絵文字類は除去（軽い顔文字はそのままにしたいので最低限に）
    text = _EMOJI_RE.sub("", text)
    # 改行→短いポーズ
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = [html.escape(p.strip()) for p in text.split("\n") if p.strip()]
    # 空になったら保険
    if not parts:
        parts = [html.escape("うまく説明できなかったよ。別の言い方で聞いてみてね。")]
    # 句点が無い行に句点を付与（TTS の無音回避）
    norm = []
    for p in parts:
        if not p.endswith(("。", "！", "？", "!", "?", "…")):
            p += "。"
        norm.append(f"<p>{p}</p>")
    ssml = "<speak>" + "<break time=\"200ms\"/>".join(norm) + "</speak>"
    # デバッグしやすいように長さログ
    LOGGER.debug(f"[SSML] len={len(ssml)} preview={ssml[:240]}")
    # Alexa 制限（約8000字）をだいぶ下回るが、念のため切り詰め
    if len(ssml) > 7000:
        ssml = ssml[:6900] + "</speak>"
    return ssml

# ---------- 共通ユーティリティ ----------
def _now() -> float:
    return time.time()

def _deadline_exceeded(start: float) -> bool:
    return (_now() - start) >= HARD_DEADLINE_SEC

def _get_session(handler_input: HandlerInput) -> Dict[str, Any]:
    return handler_input.attributes_manager.session_attributes

def _append_history(session: Dict[str, Any], role: str, text: str) -> None:
    hist: List[Dict[str, str]] = session.get("history", [])
    hist.append({"role": role, "text": (text or "").strip()})
    trimmed = [t for t in hist if t.get("role") in ("user", "assistant")]
    if len(trimmed) > MAX_HISTORY_TURNS * 2:
        trimmed = trimmed[-MAX_HISTORY_TURNS * 2:]
    session["history"] = trimmed

def _last_user_utterance(session: Dict[str, Any]) -> str:
    hist = session.get("history", [])
    for t in reversed(hist):
        if t.get("role") == "user":
            return t.get("text") or ""
    return ""

def _build_chat_messages(session: Dict[str, Any], user_query: str) -> List[Dict[str, str]]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    msgs.append({"role": "user", "content": FEWSHOT_USER})
    msgs.append({"role": "assistant", "content": FEWSHOT_ASSISTANT})
    for t in session.get("history", []):
        r, text = t.get("role"), (t.get("text") or "").strip()
        if r in ("user", "assistant") and text:
            msgs.append({"role": r, "content": text[:200]})
    msgs.append({"role": "user", "content": (user_query or "").strip()[:400]})
    return msgs

def _one_shot(session: Dict[str, Any], user_query: str) -> str:
    client = get_openai_client_from_utils(timeout_sec=HTTP_TIMEOUT_SEC)
    messages = _build_chat_messages(session, user_query)
    return call_openai_chat_once(client, OPENAI_MODEL, messages, timeout_sec=HTTP_TIMEOUT_SEC)

# ---------- Handlers ----------
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        s = _get_session(handler_input)
        s["history"] = []
        s["pending_prompt"] = None
        return handler_input.response_builder.speak(to_safe_ssml(LAUNCH_SPEECH)).ask(to_safe_ssml(GENERIC_REPROMPT)).response

class GenericQueryIntentsHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        req_intent = getattr(getattr(handler_input.request_envelope, "request", None), "intent", None)
        name = getattr(req_intent, "name", "")
        return name in INTENTS_WITH_QUERY

    def handle(self, handler_input: HandlerInput) -> Response:
        start = _now()
        s = _get_session(handler_input)

        req_intent = handler_input.request_envelope.request.intent
        slot_map = getattr(req_intent, "slots", {}) or {}
        user_query = (slot_map.get("query").value if "query" in slot_map and slot_map["query"] else "") or ""
        LOGGER.debug(f"[GenericQuery] intent={req_intent.name} query='{user_query}'")

        if _deadline_exceeded(start):
            s["pending_prompt"] = user_query
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("『続けて』と言ってね。")).response

        answer = _one_shot(s, user_query)

        if answer:
            _append_history(s, "user", user_query)
            _append_history(s, "assistant", answer)
            s["pending_prompt"] = None
            return handler_input.response_builder.speak(to_safe_ssml(answer)).ask(to_safe_ssml(GENERIC_REPROMPT)).response
        else:
            s["pending_prompt"] = user_query
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("『続けて』と言ってね。")).response

class RefineIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("RefineIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        start = _now()
        s = _get_session(handler_input)
        intent = handler_input.request_envelope.request.intent
        slot = intent.slots.get("filter") if intent and intent.slots else None
        filt = (slot.value if slot else "") or ""
        base = s.get("pending_prompt") or _last_user_utterance(s)
        if not base:
            base = filt
        refined = f"{base}。ただし条件は「{filt}」。要点だけ短く。"

        if _deadline_exceeded(start):
            s["pending_prompt"] = refined
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("『続けて』と言ってね。")).response

        answer = _one_shot(s, refined)
        if answer:
            _append_history(s, "user", refined)
            _append_history(s, "assistant", answer)
            s["pending_prompt"] = None
            return handler_input.response_builder.speak(to_safe_ssml(answer)).ask(to_safe_ssml(GENERIC_REPROMPT)).response
        else:
            s["pending_prompt"] = refined
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("『続けて』と言ってね。")).response

class ContinuationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("ContinuationIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        start = _now()
        s = _get_session(handler_input)
        intent = handler_input.request_envelope.request.intent
        slot = intent.slots.get("query") if intent and intent.slots else None
        q_from_slot = (slot.value if slot else "") or ""

        pending = (s.get("pending_prompt") or "").strip()
        if not pending:
            base = q_from_slot or _last_user_utterance(s)
            if not base:
                return handler_input.response_builder.speak(to_safe_ssml("今は続ける内容がないみたい。何を知りたい？")).ask(to_safe_ssml(GENERIC_REPROMPT)).response
            pending = base + "。続きと詳細を短く。"

        if _deadline_exceeded(start):
            s["pending_prompt"] = pending
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("もう一度『続けて』と言ってね。")).response

        answer = _one_shot(s, pending)
        if answer:
            _append_history(s, "user", pending)
            _append_history(s, "assistant", answer)
            s["pending_prompt"] = None
            return handler_input.response_builder.speak(to_safe_ssml(answer)).ask(to_safe_ssml(GENERIC_REPROMPT)).response
        else:
            s["pending_prompt"] = pending
            return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("もう一度『続けて』と言ってね。")).response

class TestIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("TestIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("やっほー！ぴこは元気だよ。試してくれてありがとう！")).ask(to_safe_ssml(GENERIC_REPROMPT)).response

class AcknowledgmentIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        # 相づち系 or YesIntent（YesIntentをモデルに足した場合にも対応）
        return (is_intent_name("AcknowledgmentIntent")(handler_input)
                or is_intent_name("AMAZON.YesIntent")(handler_input))

    def handle(self, handler_input: HandlerInput) -> Response:
        # ★ 相づち = 「続けて」の意味で解釈
        start = _now()
        s = _get_session(handler_input)

        # Continuation と同じロジックを再利用
        pending = (s.get("pending_prompt") or "").strip()
        if not pending:
            base = _last_user_utterance(s)
            if not base:
                # 直前の文脈が無いなら、従来の相づち応答へ
                return (handler_input.response_builder
                        .speak(to_safe_ssml("わかったよ。今は何を知りたい？"))
                        .ask(to_safe_ssml(GENERIC_REPROMPT))
                        .response)
            pending = base + "。続きと詳細を短く。"

        if _deadline_exceeded(start):
            s["pending_prompt"] = pending
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ERROR_SPEECH))
                    .ask(to_safe_ssml("もう一度『続けて』と言ってね。"))
                    .response)

        answer = _one_shot(s, pending)
        if answer:
            _append_history(s, "user", pending)
            _append_history(s, "assistant", answer)
            s["pending_prompt"] = None
            return (handler_input.response_builder
                    .speak(to_safe_ssml(answer))
                    .ask(to_safe_ssml(GENERIC_REPROMPT))
                    .response)
        else:
            s["pending_prompt"] = pending
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ERROR_SPEECH))
                    .ask(to_safe_ssml("もう一度『続けて』と言ってね。"))
                    .response)

class FallbackHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("うまく聞き取れなかった。もう一度お願い。")).ask(to_safe_ssml(GENERIC_REPROMPT)).response

class HelpHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("知りたい言葉を言ってね。たとえば『生成AIについて教えて』だよ。")).ask(to_safe_ssml(GENERIC_REPROMPT)).response

class StopCancelHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.StopIntent")(handler_input) or is_intent_name("AMAZON.CancelIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("またね！")).response

class NavigateHomeHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.NavigateHomeIntent")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("ホームに戻ったよ。知りたいことをどうぞ！")).ask(to_safe_ssml(GENERIC_REPROMPT)).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)
    def handle(self, handler_input: HandlerInput) -> Response:
        LOGGER.info(">>> SessionEndedRequest")
        return handler_input.response_builder.response

class AnyRequestTypeHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return True
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True
    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        LOGGER.exception(f"[Exception] {exception}")
        return handler_input.response_builder.speak(to_safe_ssml(ERROR_SPEECH)).ask(to_safe_ssml("『続けて』と言ってね。")).response

# ルーティング
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(RefineIntentHandler())
sb.add_request_handler(GenericQueryIntentsHandler())
sb.add_request_handler(ContinuationIntentHandler())
sb.add_request_handler(TestIntentHandler())
sb.add_request_handler(AcknowledgmentIntentHandler())
sb.add_request_handler(HelpHandler())
sb.add_request_handler(StopCancelHandler())
sb.add_request_handler(NavigateHomeHandler())
sb.add_request_handler(FallbackHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(AnyRequestTypeHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
