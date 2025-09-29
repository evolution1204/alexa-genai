# -*- coding: utf-8 -*-
import json
import time
from typing import List, Dict, Any

import boto3
from config import S3_BUCKET, S3_PREFIX

s3 = boto3.client("s3")

# ==== ユーザー別の簡易KV（TestIntent等） ====
def _user_key(handler_input) -> str:
    uid = handler_input.request_envelope.context.system.user.user_id or "anon"
    return f"{S3_PREFIX}/pico_persist/{uid}.json"

def s3_store_load_user(handler_input) -> Dict[str, Any]:
    key = _user_key(handler_input)
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        return {}
    except Exception:
        return {}

def s3_store_save_user(handler_input, data: Dict[str, Any]) -> None:
    key = _user_key(handler_input)
    s3.put_object(
        Bucket=S3_BUCKET, Key=key,
        Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json; charset=utf-8"
    )

# ==== RAG（ユーザー別の軽量メモ） ====
_RAG_DIR = f"{S3_PREFIX}/pico_rag"

def _rag_key(handler_input) -> str:
    uid = handler_input.request_envelope.context.system.user.user_id or "anon"
    return f"{_RAG_DIR}/{uid}.json"

def _rag_load(handler_input) -> List[Dict[str, Any]]:
    key = _rag_key(handler_input)
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        return []
    except Exception:
        return []

def _rag_save(handler_input, items: List[Dict[str, Any]]) -> None:
    key = _rag_key(handler_input)
    s3.put_object(
        Bucket=S3_BUCKET, Key=key,
        Body=json.dumps(items, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json; charset=utf-8"
    )

def rag_add_items(handler_input, new_items: List[Dict[str, Any]], max_items: int = 40, snippet_max: int = 300):
    cur  = _rag_load(handler_input)
    seen = {(it.get("url"), it.get("title")) for it in cur}
    ts   = int(time.time())
    for it in new_items:
        title   = (it.get("title") or "無題").strip()[:120]
        url     = (it.get("url") or "").strip()
        snippet = (it.get("snippet") or title)[:snippet_max]
        if (url, title) not in seen:
            cur.append({"title": title, "url": url, "snippet": snippet, "ts": ts})
    cur = cur[-max_items:]
    _rag_save(handler_input, cur)

def rag_top_snippets(handler_input, k: int = 5) -> List[str]:
    items = _rag_load(handler_input)
    return [f"■{it['title']}｜抜粋: {it['snippet']}" for it in items[-k:]]

# ==== 直近のNotion検索結果（本文なし：id/title/urlのみ） ====
_NOTION_LAST_DIR = f"{S3_PREFIX}/pico_notion"

def _notion_last_key(handler_input) -> str:
    uid = handler_input.request_envelope.context.system.user.user_id or "anon"
    return f"{_NOTION_LAST_DIR}/{uid}.json"

def save_last_notion_results(handler_input, items: List[Dict[str, str]]) -> None:
    key = _notion_last_key(handler_input)
    payload = [{"id": it.get("id"), "title": it.get("title"), "url": it.get("url")} for it in items]
    s3.put_object(
        Bucket=S3_BUCKET, Key=key,
        Body=json.dumps({"items": payload, "ts": int(time.time())}, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json; charset=utf-8"
    )

def load_last_notion_results(handler_input) -> List[Dict[str, str]]:
    key = _notion_last_key(handler_input)
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        data = json.loads(obj["Body"].read().decode("utf-8"))
        return data.get("items", []) or []
    except s3.exceptions.NoSuchKey:
        return []
    except Exception:
        return []
