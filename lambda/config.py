# -*- coding: utf-8 -*-
"""
config.py
- 優先順: os.environ > .env > デフォルト
- .env は /var/task/.env に配置（Alexa Hosted はコードと一緒にアップ）
- 値が無い重要キーはログ警告のみ（動作は継続）
"""
import os
import logging

LOGGER = logging.getLogger(__name__)

def _load_dotenv_if_present():
    path = "/var/task/.env"
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if (not k) or (k in os.environ):
                    continue
                if (v.startswith(("'", '"')) and v.endswith(("'", '"')) and len(v) >= 2):
                    v = v[1:-1]
                os.environ[k] = v
    except Exception as e:
        LOGGER.warning(f"[config] .env load skipped (ex={type(e).__name__})")

# 先に .env を読み込んでおく
_load_dotenv_if_present()

# ====== 主要キー ======
OPENAI_API_KEY  = os.environ.get("_OPENAI_API_KEY", "").strip()
OPENAI_MODEL    = os.environ.get("OPENAI_MODEL", "gpt-5-chat-latest").strip()

NOTION_TOKEN    = os.environ.get("NOTION_TOKEN", "").strip()
NOTION_VERSION  = os.environ.get("NOTION_VERSION", "2022-06-28").strip()

S3_BUCKET       = os.environ.get("S3_BUCKET", "").strip()
S3_PREFIX       = os.environ.get("S3_PREFIX", "Media").strip()

# ====== チューニング値 ======
HTTP_TIMEOUT_SEC       = float(os.environ.get("HTTP_TIMEOUT_SEC", "2.0"))
HARD_DEADLINE_SEC      = float(os.environ.get("HARD_DEADLINE_SEC", "4.8"))
MAX_HISTORY_TURNS      = int(os.environ.get("MAX_HISTORY_TURNS", "6"))
NOTION_SEARCH_LIMIT    = int(os.environ.get("NOTION_SEARCH_LIMIT", "3"))
NOTION_BLOCKS_PAGE_SZ  = int(os.environ.get("NOTION_BLOCKS_PAGE_SZ", "20"))
NOTION_SNIPPET_CHARS   = int(os.environ.get("NOTION_SNIPPET_CHARS", "300"))

def warn_if_missing():
    if not OPENAI_API_KEY:
        LOGGER.warning("[config] _OPENAI_API_KEY is missing")
    if not NOTION_TOKEN:
        LOGGER.warning("[config] NOTION_TOKEN is missing")
    if not S3_BUCKET:
        LOGGER.warning("[config] S3_BUCKET is missing (S3連携が失敗します)")
