# -*- coding: utf-8 -*-
import os
from typing import Optional, List, Dict
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
import httpx

import logging
_logger = logging.getLogger(__name__)

_DEFAULT_HTTP_TIMEOUT = 2.5  # 8s対策：1回の外部呼び出しは2.5秒で切る
_MAX_TOKENS = 80             # 音声向けにさらに短く（Alexaは8秒制限）

def _get_openai_api_key() -> str:
    """環境変数からAPIキーを取得（遅延評価：config.pyで.envを読み込んだ後に取得）"""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        _logger.info(f"OpenAI API Key loaded: {api_key[:10]}...{api_key[-4:]}")
    else:
        _logger.error("OpenAI API Key is empty!")
    return api_key

def get_openai_client_from_utils(timeout_sec: Optional[float] = None) -> OpenAI:
    timeout = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    api_key = _get_openai_api_key()  # 関数呼び出し時に取得（config.py実行後）

    # httpxクライアントを明示的に作成してタイムアウトを強制
    http_client = httpx.Client(
        timeout=httpx.Timeout(timeout, connect=5.0)
    )

    return OpenAI(api_key=api_key, http_client=http_client)

def call_openai_chat_once(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    *,
    timeout_sec: Optional[float] = None,
    max_tokens: int = _MAX_TOKENS,
) -> str:
    """Chat Completions を1回だけ呼ぶ（失敗時は空文字で返す）。"""
    import logging
    logger = logging.getLogger(__name__)

    t = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    logger.info(f"[UTILS] Calling OpenAI API: model={model}, timeout={t}s, max_tokens={max_tokens}")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            timeout=t
        )
        text = (resp.choices[0].message.content or "").strip()
        logger.info(f"[UTILS] OpenAI API success: response length={len(text)}")
        return text
    except (APITimeoutError, RateLimitError, APIError, Exception) as e:
        logger.error(f"[UTILS] OpenAI API Error: {type(e).__name__}: {str(e)}")
        return ""  # 上位で即収束し「続けて」を促す
