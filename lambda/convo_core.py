# -*- coding: utf-8 -*-
import re
import time
import html
import logging
from typing import List, Dict, Any, Optional

from utils import get_openai_client_from_utils, call_openai_chat_once
from config import (
    OPENAI_MODEL, HTTP_TIMEOUT_SEC, HARD_DEADLINE_SEC, MAX_HISTORY_TURNS, warn_if_missing
)

LOGGER = logging.getLogger(__name__)
warn_if_missing()  # 起動時に一度だけ警告

LAUNCH_SPEECH    = "ぴこだよ。なんでも聞いてみて！"
GENERIC_REPROMPT = "他に質問あるかな？『続けて』で詳しくも話せるよ。"
ERROR_SPEECH     = "ごめん、いまはうまく答えを取れなかった。『続けて』で試せるよ。"

SYSTEM_PROMPT = (
    "あなたは『ぴこ』。日本語で話す、元気で可愛い相棒アシスタント。"
    "【性格/口調】一人称は「ぼく」。語尾はやわらかく（〜だよ/〜だね/〜かな）。"
    "【話し方ルール】"
    "1) 最初は50〜100字で要点"
    "2) 絵文字・顔文字・装飾記号（矢印/記号/記号絵）・URLは出さない。"
    "3) 難しい語は噛み砕く。"
    "4) 具体例は短く。"
    "5) 次の提案が必要なら一言添える。"
    "【NG】尊大/ぶっきらぼう/機械的/過度に事務的な敬体/絵文字の連打/長すぎる前置き。"
)
FEWSHOT_USER      = "自己紹介して"
FEWSHOT_ASSISTANT = "やっほー、ぼくは『ぴこ』だよ！短くわかりやすくお手伝いするね。何から話そっか？"

# ---------- SSML ----------
_URL_RE   = re.compile(r'https?://\S+')
_CTRL_RE  = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]')
_EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF\U0001F1E6-\U0001F1FF]+", flags=re.UNICODE)

def to_safe_ssml(text: str) -> str:
    if not text:
        text = "……"
    text = _CTRL_RE.sub("", text)
    text = _URL_RE.sub("リンク", text)
    text = _EMOJI_RE.sub("", text)
    parts = [html.escape(p.strip()) for p in text.split("\n") if p.strip()]
    if not parts:
        parts = [html.escape("うまく説明できなかったよ。別の言い方で聞いてみてね。")]
    norm = []
    for p in parts:
        if not p.endswith(("。","！","？","!","?","…")):
            p += "。"
        norm.append(f"<p>{p}</p>")
    ssml = "<speak>" + "<break time=\"200ms\"/>".join(norm) + "</speak>"
    if len(ssml) > 7000:
        ssml = ssml[:6900] + "</speak>"
    return ssml

# ---------- 共通 ----------
def _now() -> float:
    return time.time()

def _deadline_exceeded(start: float) -> bool:
    return (_now() - start) >= HARD_DEADLINE_SEC

def _get_session(handler_input) -> Dict[str, Any]:
    return handler_input.attributes_manager.session_attributes

def _append_history(session: Dict[str, Any], role: str, text: str) -> None:
    hist = session.get("history", [])
    hist.append({"role": role, "text": (text or "").strip()})
    trimmed = [t for t in hist if t.get("role") in ("user", "assistant")]
    if len(trimmed) > MAX_HISTORY_TURNS * 2:
        trimmed = trimmed[-MAX_HISTORY_TURNS * 2:]
    session["history"] = trimmed

def _last_user_utterance(session: Dict[str, Any]) -> str:
    for t in reversed(session.get("history", [])):
        if t.get("role") == "user":
            return t.get("text") or ""
    return ""

# ---------- OpenAI ----------
def _build_chat_messages(session: Dict[str, Any], user_query: str, snippets: Optional[list] = None) -> List[Dict[str, str]]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if snippets:
        msgs.append({"role": "system", "content": "参照ノート:\n" + "\n".join(snippets)})
    msgs.append({"role": "user", "content": FEWSHOT_USER})
    msgs.append({"role": "assistant", "content": FEWSHOT_ASSISTANT})
    for t in session.get("history", []):
        if t.get("role") in ("user","assistant") and (t.get("text") or "").strip():
            msgs.append({"role": t["role"], "content": t["text"][:200]})
    msgs.append({"role": "user", "content": (user_query or "").strip()[:400]})
    return msgs

def one_shot_answer(session: Dict[str, Any], user_query: str, snippets: Optional[list] = None) -> str:
    client = get_openai_client_from_utils(timeout_sec=HTTP_TIMEOUT_SEC)
    messages = _build_chat_messages(session, user_query, snippets)
    return call_openai_chat_once(client, OPENAI_MODEL, messages, timeout_sec=HTTP_TIMEOUT_SEC)
