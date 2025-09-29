# -*- coding: utf-8 -*-
import json
import requests

from config import (
    NOTION_TOKEN, NOTION_VERSION, HTTP_TIMEOUT_SEC,
    NOTION_SEARCH_LIMIT, NOTION_BLOCKS_PAGE_SZ, NOTION_SNIPPET_CHARS
)

def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

def _extract_title_from_page(page):
    props = page.get("properties", {}) or []
    if isinstance(props, dict):
        for p in props.values():
            if p and p.get("type") == "title":
                rich = p.get("title") or []
                return "".join([seg.get("plain_text","") for seg in rich]).strip() or "無題"
    return "無題"

def notion_search_pages(query: str, *, limit: int = None, timeout: float = None):
    """検索は既定で .env の NOTION_SEARCH_LIMIT 件（通常3）。本文は取得しない。"""
    if limit is None:
        limit = NOTION_SEARCH_LIMIT
    if timeout is None:
        timeout = HTTP_TIMEOUT_SEC

    url = "https://api.notion.com/v1/search"
    payload = {
        "query": query or "",
        "page_size": limit,
        "filter": {"value": "page", "property": "object"},
        "sort": {"direction": "descending", "timestamp": "last_edited_time"}
    }
    try:
        resp = requests.post(url, headers=_notion_headers(), data=json.dumps(payload), timeout=timeout)
        if resp.status_code != 200:
            return []
        results = resp.json().get("results", []) or []
        out = []
        for it in results[:limit]:
            if it.get("object") != "page":
                continue
            title = _extract_title_from_page(it)
            page_url = it.get("url") or ""
            out.append({"id": it.get("id"), "title": title, "url": page_url})
        return out
    except Exception:
        return []

BLOCK_TYPES_WITH_TEXT = {
    "paragraph","heading_1","heading_2","heading_3",
    "to_do","bulleted_list_item","numbered_list_item",
    "quote","callout","toggle"
}

def _rich_text_to_plain(rt):
    return "".join([(r.get("plain_text") or "") for r in (rt or [])])

def _block_to_text(block):
    btype = block.get("type")
    if btype in BLOCK_TYPES_WITH_TEXT:
        return _rich_text_to_plain(block.get(btype,{}).get("rich_text"))
    return ""

def notion_page_first_text(page_id: str, *, max_chars: int = None, timeout: float = None) -> str:
    if max_chars is None:
        max_chars = NOTION_SNIPPET_CHARS
    if timeout is None:
        timeout = HTTP_TIMEOUT_SEC

    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size={NOTION_BLOCKS_PAGE_SZ}"
    try:
        resp = requests.get(url, headers=_notion_headers(), timeout=timeout)
        if resp.status_code != 200:
            return ""
        blocks = resp.json().get("results", []) or []
        lines = []
        total = 0
        for b in blocks:
            t = _block_to_text(b).strip()
            if t:
                lines.append(t)
                total += len(t)
                if total >= int(max_chars * 1.5):
                    break
        return " ／ ".join(lines)[:max_chars]
    except Exception:
        return ""
