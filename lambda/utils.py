# -*- coding: utf-8 -*-
import os
from typing import Optional, List, Dict
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# 環境変数からAPIキーを取得（本番はSecretsまたは環境変数を使用）
_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

_DEFAULT_HTTP_TIMEOUT = 3.0  # 8s対策：1回の外部呼び出しは3秒で切る
_MAX_TOKENS = 120            # 音声向けに短め

def get_openai_client_from_utils(timeout_sec: Optional[float] = None) -> OpenAI:
    timeout = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    # ここは古いSDKでも通る安全な引数のみ
    return OpenAI(api_key=_OPENAI_API_KEY, timeout=timeout)

def call_openai_chat_once(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    *,
    timeout_sec: Optional[float] = None,
    max_tokens: int = _MAX_TOKENS,
) -> str:
    """Chat Completions を1回だけ呼ぶ（失敗時は空文字で返す）。"""
    t = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            timeout=t
        )
        text = (resp.choices[0].message.content or "").strip()
        return text
    except (APITimeoutError, RateLimitError, APIError, Exception):
        return ""  # 上位で即収束し「続けて」を促す
