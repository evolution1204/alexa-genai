# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response

from convo_core import (
    LAUNCH_SPEECH, GENERIC_REPROMPT, ERROR_SPEECH,
    _now, _deadline_exceeded, to_safe_ssml,
    _get_session, _append_history, _last_user_utterance,
    one_shot_answer
)
from notion_utils import (
    notion_search_pages, notion_page_first_text,
    notion_create_page, notion_add_to_database
)
from rag_store_s3 import (
    s3_store_load_user, s3_store_save_user,
    rag_add_items, rag_top_snippets,
    save_last_notion_results, load_last_notion_results
)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.debug("### HANDLER READY")

INTENTS_WITH_QUERY = {
    "GptQueryIntent", "CreativeIntent", "EntertainmentIntent", "EmotionalIntent",
    "AnalysisIntent", "HelpIntent", "PhilosophicalIntent", "PracticalIntent",
    "DetailRequestIntent", "NavigationIntent", "SelectionIntent",
}
NOTION_SEARCH_INTENT = "NotionSearchIntent"
NOTION_READ_INTENT   = "NotionReadIntent"

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input) -> Response:
        s = _get_session(handler_input)
        s["history"] = []
        s["pending_prompt"] = None
        return (handler_input.response_builder
                .speak(to_safe_ssml(LAUNCH_SPEECH))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class GenericQueryIntentsHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = getattr(getattr(handler_input.request_envelope, "request", None), "intent", None)
        return getattr(req, "name", "") in INTENTS_WITH_QUERY
    def handle(self, handler_input) -> Response:
        s = _get_session(handler_input)
        intent = handler_input.request_envelope.request.intent
        LOGGER.info(f">>> GenericQueryIntentsHandler: intent={intent.name}")
        slots: Dict[str, Any] = getattr(intent, "slots", {}) or {}
        q = (slots.get("query").value if "query" in slots and slots["query"] else "") or ""
        LOGGER.info(f">>> Query: {q}")
        LOGGER.info(f">>> RAG: Starting snippet retrieval...")
        snippets = rag_top_snippets(handler_input, k=5)
        LOGGER.info(f">>> RAG: Retrieved {len(snippets) if snippets else 0} snippets")
        LOGGER.info(f">>> Calling LLM API...")
        ans = one_shot_answer(session=s, user_query=q, snippets=snippets)
        LOGGER.info(f">>> LLM response: {ans[:50] if ans else 'empty'}")
        if ans:
            _append_history(s, "user", q)
            _append_history(s, "assistant", ans)
            s["pending_prompt"] = None
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ans))
                    .ask(to_safe_ssml(GENERIC_REPROMPT))
                    .response)
        return (handler_input.response_builder
                .speak(to_safe_ssml(ERROR_SPEECH))
                .ask(to_safe_ssml("『続けて』と言ってね。"))
                .response)

class NotionSearchIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name(NOTION_SEARCH_INTENT)(handler_input)
    def handle(self, handler_input) -> Response:
        intent = handler_input.request_envelope.request.intent
        slots: Dict[str, Any] = getattr(intent, "slots", {}) or {}
        q = (slots.get("query").value if "query" in slots and slots["query"] else "") or ""
        items = notion_search_pages(q)
        if items:
            save_last_notion_results(handler_input, items)
            rag_add_items(handler_input, [{"title":it["title"],"url":it["url"],"snippet":it["title"]} for it in items])
            lines = [f"{i+1}件目、{it['title']}" for i, it in enumerate(items)]
            speech = "Notionの上位3件だよ。 " + " ".join(lines) + "。本文が必要なら『1件目の本文を読んで』みたいに言ってね。"
        else:
            speech = f"Notionで「{q}」は見つからなかったよ。"
        return (handler_input.response_builder
                .speak(to_safe_ssml(speech))
                .ask(to_safe_ssml("ほかに探す？"))
                .response)

class NotionReadIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name(NOTION_READ_INTENT)(handler_input)
    def handle(self, handler_input) -> Response:
        import math
        intent = handler_input.request_envelope.request.intent
        slots: Dict[str, Any] = getattr(intent, "slots", {}) or {}

        idx = None
        if "index" in slots and slots["index"] and slots["index"].value:
            try:
                idx = int(slots["index"].value)
            except Exception:
                idx = None

        title_hint = (slots.get("title").value if "title" in slots and slots["title"] else "") or ""
        position   = (slots.get("position").value if "position" in slots and slots["position"] else "") or ""

        items = load_last_notion_results(handler_input)
        if not items:
            speech = "直近の検索結果が見つからないよ。まず『Notionで ◯◯ を探して』と言ってみてね。"
            return (handler_input.response_builder
                    .speak(to_safe_ssml(speech))
                    .ask(to_safe_ssml(GENERIC_REPROMPT))
                    .response)

        if idx is None and position:
            n = len(items)
            pos = position.strip()
            if pos in ("最初", "いちばん最初", "先頭", "はじめ"):
                idx = 1
            elif pos in ("真ん中", "中間", "なか"):
                idx = max(1, min(n, math.ceil(n/2.0)))
            elif pos in ("最後", "いちばん最後", "末尾", "ラスト"):
                idx = n

        target = None
        if idx is not None and 1 <= idx <= len(items):
            target = items[idx-1]
        if (not target) and title_hint:
            low = title_hint.strip().lower()
            for it in items:
                if (it.get("title") or "").lower().startswith(low):
                    target = it
                    break

        if not target:
            names = "、".join([f"{i+1}件目 {it['title']}" for i, it in enumerate(items)])
            speech = f"どれを読む？ 候補は、{names}。『最初の本文を読んで』や『1件目の本文を読んで』みたいに言ってね。"
            return (handler_input.response_builder
                    .speak(to_safe_ssml(speech))
                    .ask(to_safe_ssml("番号か位置でどうぞ。"))
                    .response)

        pid = (target.get("id") or "").replace("-", "")
        snippet = notion_page_first_text(pid) if pid else ""
        if not snippet:
            speech = f"『{target.get('title')}』の本文は今うまく取れなかったよ。"
        else:
            rag_add_items(handler_input, [{
                "title": target.get("title"),
                "url": target.get("url"),
                "snippet": snippet
            }])
            speech = f"『{target.get('title')}』の要点だよ。{snippet}"

        return (handler_input.response_builder
                .speak(to_safe_ssml(speech))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class TestIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("TestIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        d = s3_store_load_user(handler_input)
        cnt = int(d.get("ping_count", 0)) + 1
        d["ping_count"] = cnt
        d["last_check"] = int(_now())
        try:
            s3_store_save_user(handler_input, d)
            msg = f"S3保存 OK。通し番号は {cnt} 回目だよ。"
        except Exception as e:
            msg = f"S3保存 NG（ex={type(e).__name__}）。"
        return (handler_input.response_builder
                .speak(to_safe_ssml(msg))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class RefineIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RefineIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        s = _get_session(handler_input)
        intent = handler_input.request_envelope.request.intent
        slot = intent.slots.get("filter") if intent and intent.slots else None
        filt = (slot.value if slot else "") or ""
        base = s.get("pending_prompt") or _last_user_utterance(s) or filt
        refined = f"{base}。ただし条件は「{filt}」。要点だけ短く。"

        start = _now()
        if _deadline_exceeded(start):
            s["pending_prompt"] = refined
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ERROR_SPEECH))
                    .ask(to_safe_ssml("『続けて』と言ってね。"))
                    .response)

        ans = one_shot_answer(s, refined, snippets=rag_top_snippets(handler_input, k=5))
        if ans:
            _append_history(s, "user", refined)
            _append_history(s, "assistant", ans)
            s["pending_prompt"] = None
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ans))
                    .ask(to_safe_ssml(GENERIC_REPROMPT))
                    .response)

        s["pending_prompt"] = refined
        return (handler_input.response_builder
                .speak(to_safe_ssml(ERROR_SPEECH))
                .ask(to_safe_ssml("『続けて』と言ってね。"))
                .response)

class ContinuationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ContinuationIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        s = _get_session(handler_input)
        intent = handler_input.request_envelope.request.intent
        slot = intent.slots.get("query") if intent and intent.slots else None
        q_from_slot = (slot.value if slot else "") or ""

        pending = (s.get("pending_prompt") or "").strip()
        if not pending:
            base = q_from_slot or _last_user_utterance(s)
            if not base:
                return (handler_input.response_builder
                        .speak(to_safe_ssml("今は続ける内容がないみたい。何を知りたい？"))
                        .ask(to_safe_ssml(GENERIC_REPROMPT))
                        .response)
            pending = base + "。続きと詳細を短く。"

        start = _now()
        if _deadline_exceeded(start):
            s["pending_prompt"] = pending
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ERROR_SPEECH))
                    .ask(to_safe_ssml("もう一度『続けて』と言ってね。"))
                    .response)

        ans = one_shot_answer(s, pending, snippets=rag_top_snippets(handler_input, k=5))
        if ans:
            _append_history(s, "user", pending)
            _append_history(s, "assistant", ans)
            s["pending_prompt"] = None
            return (handler_input.response_builder
                    .speak(to_safe_ssml(ans))
                    .ask(to_safe_ssml(GENERIC_REPROMPT))
                    .response)

        s["pending_prompt"] = pending
        return (handler_input.response_builder
                .speak(to_safe_ssml(ERROR_SPEECH))
                .ask(to_safe_ssml("もう一度『続けて』と言ってね。"))
                .response)

class HelpHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        return (handler_input.response_builder
                .speak(to_safe_ssml("知りたい言葉を言ってね。たとえば『生成AIについて教えて』だよ。"))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class StopCancelHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.StopIntent")(handler_input)
                or is_intent_name("AMAZON.CancelIntent")(handler_input))
    def handle(self, handler_input) -> Response:
        return handler_input.response_builder.speak(to_safe_ssml("またね！")).response

class NotionCreatePageIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NotionCreatePageIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        intent = handler_input.request_envelope.request.intent
        slots: Dict[str, Any] = getattr(intent, "slots", {}) or {}

        content = (slots.get("content").value if "content" in slots and slots["content"] else "") or ""

        if not content:
            speech = "内容を教えてね。"
            return (handler_input.response_builder
                    .speak(to_safe_ssml(speech))
                    .ask(to_safe_ssml(speech))
                    .response)

        # コンテンツの最初の30文字をタイトルにする
        title = content[:30] if len(content) > 30 else content

        # Notionページ作成
        result = notion_create_page(title=title, content=content)

        if result["success"]:
            speech = f"Notionに「{title}」を保存したよ！"
        else:
            speech = f"Notionへの保存に失敗したよ。エラー: {result['error']}"

        return (handler_input.response_builder
                .speak(to_safe_ssml(speech))
                .ask(to_safe_ssml("他に何かある？"))
                .response)

class NotionAddToDatabaseIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NotionAddToDatabaseIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        intent = handler_input.request_envelope.request.intent
        slots: Dict[str, Any] = getattr(intent, "slots", {}) or {}

        content = (slots.get("content").value if "content" in slots and slots["content"] else "") or ""

        if not content:
            speech = "内容を教えてね。"
            return (handler_input.response_builder
                    .speak(to_safe_ssml(speech))
                    .ask(to_safe_ssml(speech))
                    .response)

        # コンテンツの最初の30文字をタイトルにする
        title = content[:30] if len(content) > 30 else content

        # Notionデータベースにエントリ追加
        result = notion_add_to_database(title=title, content=content)

        if result["success"]:
            speech = f"データベースに「{title}」を追加したよ！"
        else:
            speech = f"データベースへの追加に失敗したよ。エラー: {result['error']}"

        return (handler_input.response_builder
                .speak(to_safe_ssml(speech))
                .ask(to_safe_ssml("他に何かある？"))
                .response)

class NavigateHomeHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NavigateHomeIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        return (handler_input.response_builder
                .speak(to_safe_ssml("ホームに戻ったよ。知りたいことをどうぞ！"))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class FallbackHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    def handle(self, handler_input) -> Response:
        return (handler_input.response_builder
                .speak(to_safe_ssml("うまく聞き取れなかった。もう一度お願い。"))
                .ask(to_safe_ssml(GENERIC_REPROMPT))
                .response)

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)
    def handle(self, handler_input) -> Response:
        LOGGER.info(">>> SessionEndedRequest")
        return handler_input.response_builder.response

class AnyRequestTypeHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return True
    def handle(self, handler_input) -> Response:
        req = handler_input.request_envelope.request
        rtype = getattr(req, "object_type", getattr(req, "type", "Unknown"))
        iname = getattr(getattr(req, "intent", None), "name", None)
        LOGGER.warning(f"[UNHANDLED] type={rtype} intent={iname}")
        hint = "Notionで 〇〇 を探して、と言ってみてね。"
        return (handler_input.response_builder
                .speak(to_safe_ssml("ごめん、いまの言い方では意図が取れなかったみたい。" + hint))
                .ask(to_safe_ssml("もう一度どうぞ。"))
                .response)

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True
    def handle(self, handler_input, exception) -> Response:
        LOGGER.exception(f"[Exception] {exception}")
        return (handler_input.response_builder
                .speak(to_safe_ssml(ERROR_SPEECH))
                .ask(to_safe_ssml("『続けて』と言ってね。"))
                .response)

# -------- ルーティング --------
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NotionSearchIntentHandler())
sb.add_request_handler(NotionReadIntentHandler())
sb.add_request_handler(NotionCreatePageIntentHandler())
sb.add_request_handler(NotionAddToDatabaseIntentHandler())
sb.add_request_handler(RefineIntentHandler())
sb.add_request_handler(GenericQueryIntentsHandler())
sb.add_request_handler(ContinuationIntentHandler())
sb.add_request_handler(TestIntentHandler())
sb.add_request_handler(HelpHandler())
sb.add_request_handler(StopCancelHandler())
sb.add_request_handler(NavigateHomeHandler())
sb.add_request_handler(FallbackHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(AnyRequestTypeHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
