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
LOGGER.setLevel(logging.INFO)  # Force INFO level for debugging

def _load_dotenv_if_present():
    # Debug: List all files in /var/task
    print("[CONFIG DEBUG] Starting .env file search...")
    try:
        import glob
        all_files = glob.glob("/var/task/**/*", recursive=True)
        env_files = [f for f in all_files if f.endswith(".env")]
        print(f"[CONFIG DEBUG] All .env files found: {env_files}")
        LOGGER.info(f"All .env files found: {env_files}")
    except Exception as e:
        print(f"[CONFIG DEBUG] Error listing files: {e}")
        LOGGER.error(f"Error listing files: {e}")

    # Try multiple possible paths
    possible_paths = [
        "/var/task/.env",
        "/var/task/lambda/.env",
        os.path.join(os.path.dirname(__file__), ".env")
    ]

    path = None
    for p in possible_paths:
        print(f"[CONFIG DEBUG] Checking for .env file at: {p}")
        LOGGER.info(f"Checking for .env file at: {p}")
        if os.path.exists(p):
            path = p
            print(f"[CONFIG DEBUG] Found .env file at: {path}")
            LOGGER.info(f"Found .env file at: {path}")
            break

    if not path:
        print(f"[CONFIG DEBUG] .env file not found in any of: {possible_paths}")
        print(f"[CONFIG DEBUG] Current file location: {__file__}")
        print(f"[CONFIG DEBUG] Current directory: {os.getcwd()}")
        LOGGER.warning(f".env file not found in any of: {possible_paths}")
        LOGGER.info(f"Current file location: {__file__}")
        LOGGER.info(f"Current directory: {os.getcwd()}")
        return
    try:
        LOGGER.info(f"Loading .env file from {path}")
        with open(path, "r", encoding="utf-8") as f:
            loaded_count = 0
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
                loaded_count += 1
                LOGGER.info(f"Loaded env var: {k}")
        LOGGER.info(f"Successfully loaded {loaded_count} variables from .env")
    except Exception as e:
        LOGGER.warning(f"[config] .env load skipped (ex={type(e).__name__})")

# 先に .env を読み込んでおく
_load_dotenv_if_present()

# ====== 主要キー ======
# LLM選択（"openai" or "claude"）
LLM_PROVIDER    = os.environ.get("LLM_PROVIDER", "claude").strip().lower()
LOGGER.info(f"[CONFIG] LLM_PROVIDER loaded as: '{LLM_PROVIDER}'")

# OpenAI設定
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL    = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

# Claude設定
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL    = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929").strip()
LOGGER.info(f"[CONFIG] CLAUDE_MODEL: {CLAUDE_MODEL}, API Key exists: {bool(ANTHROPIC_API_KEY)}")

# Notion設定
NOTION_TOKEN    = os.environ.get("NOTION_TOKEN", "").strip()
NOTION_VERSION  = os.environ.get("NOTION_VERSION", "2022-06-28").strip()
NOTION_DEFAULT_PARENT_ID = os.environ.get("NOTION_DEFAULT_PARENT_ID", "").strip()
NOTION_DEFAULT_DATABASE_ID = os.environ.get("NOTION_DEFAULT_DATABASE_ID", "").strip()

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
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        LOGGER.warning("[config] OPENAI_API_KEY is missing")
    if LLM_PROVIDER == "claude" and not ANTHROPIC_API_KEY:
        LOGGER.warning("[config] ANTHROPIC_API_KEY is missing")
    if not NOTION_TOKEN:
        LOGGER.warning("[config] NOTION_TOKEN is missing")
    if not S3_BUCKET:
        LOGGER.warning("[config] S3_BUCKET is missing (S3連携が失敗します)")
