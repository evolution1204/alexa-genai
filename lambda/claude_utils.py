# -*- coding: utf-8 -*-
import os
from typing import Optional, List, Dict
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError
import httpx

import logging
_logger = logging.getLogger(__name__)

_DEFAULT_HTTP_TIMEOUT = 5.0  # Alexa 8s制限対策：APIタイムアウトは5秒
_MAX_TOKENS = 60             # 音声向けに短く（応答時間短縮）

def _get_claude_api_key() -> str:
    """環境変数からAPIキーを取得（遅延評価：config.pyで.envを読み込んだ後に取得）"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        _logger.info(f"Claude API Key loaded: {api_key[:10]}...{api_key[-4:]}")
    else:
        _logger.error("Claude API Key is empty!")
    return api_key

def get_claude_client(timeout_sec: Optional[float] = None) -> Anthropic:
    timeout = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    api_key = _get_claude_api_key()  # 関数呼び出し時に取得（config.py実行後）

    # httpxクライアントを明示的に作成してタイムアウトを強制
    http_client = httpx.Client(
        timeout=httpx.Timeout(timeout, connect=5.0)
    )

    return Anthropic(api_key=api_key, http_client=http_client)

def call_claude_chat_once(
    client: Anthropic,
    model: str,
    messages: List[Dict[str, str]],
    *,
    timeout_sec: Optional[float] = None,
    max_tokens: int = _MAX_TOKENS,
    system_prompt: Optional[str] = None
) -> str:
    """Claude Messages APIを1回だけ呼ぶ（失敗時は空文字で返す）。"""
    import logging
    logger = logging.getLogger(__name__)

    t = float(timeout_sec or _DEFAULT_HTTP_TIMEOUT)
    logger.info(f"[CLAUDE] Calling Claude API: model={model}, timeout={t}s, max_tokens={max_tokens}")

    try:
        # Anthropic APIはsystem promptを別パラメータとして渡す
        # messagesからsystem roleを除外
        api_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                # systemメッセージはsystem_promptに統合
                if system_prompt is None:
                    system_prompt = msg.get("content", "")
                else:
                    system_prompt += "\n" + msg.get("content", "")
            else:
                api_messages.append(msg)

        # Claude APIの呼び出し
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": api_messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        resp = client.messages.create(**kwargs)

        # レスポンスからテキストを抽出
        text = ""
        for block in resp.content:
            if hasattr(block, 'text'):
                text += block.text

        text = text.strip()
        logger.info(f"[CLAUDE] Claude API success: response length={len(text)}")
        return text
    except (APITimeoutError, RateLimitError, APIError, Exception) as e:
        logger.error(f"[CLAUDE] Claude API Error: {type(e).__name__}: {str(e)}")
        return ""  # 上位で即収束し「続けて」を促す
