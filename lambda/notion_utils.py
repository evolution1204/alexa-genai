# -*- coding: utf-8 -*-
import json
import requests

from config import (
    NOTION_TOKEN, NOTION_VERSION, HTTP_TIMEOUT_SEC,
    NOTION_SEARCH_LIMIT, NOTION_BLOCKS_PAGE_SZ, NOTION_SNIPPET_CHARS,
    NOTION_DEFAULT_PARENT_ID, NOTION_DEFAULT_DATABASE_ID
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

def notion_create_page(title: str, content: str, *, parent_id: str = None, timeout: float = None):
    """
    Notionに新しいページを作成

    Args:
        title: ページタイトル
        content: ページ本文
        parent_id: 親ページID（省略時は環境変数のデフォルト親ページを使用）
        timeout: タイムアウト秒数

    Returns:
        dict: {"success": bool, "page_id": str, "url": str, "error": str}
    """
    if timeout is None:
        timeout = HTTP_TIMEOUT_SEC

    if parent_id is None:
        parent_id = NOTION_DEFAULT_PARENT_ID

    if not parent_id:
        return {"success": False, "error": "親ページIDが指定されていません"}

    url = "https://api.notion.com/v1/pages"

    # ページプロパティ（タイトル）
    properties = {
        "title": {
            "title": [{"text": {"content": title}}]
        }
    }

    # 本文ブロック（段落として追加）
    children = []
    if content:
        # 長い文章は2000文字ごとに分割（Notion APIの制限）
        max_len = 2000
        content_parts = [content[i:i+max_len] for i in range(0, len(content), max_len)]
        for part in content_parts:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": part}}]
                }
            })

    payload = {
        "parent": {"page_id": parent_id},
        "properties": properties,
        "children": children
    }

    try:
        resp = requests.post(url, headers=_notion_headers(), data=json.dumps(payload), timeout=timeout)
        if resp.status_code != 200:
            error_msg = resp.json().get("message", "不明なエラー")
            return {"success": False, "error": f"API エラー: {error_msg}"}

        result = resp.json()
        return {
            "success": True,
            "page_id": result.get("id"),
            "url": result.get("url"),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": f"例外: {type(e).__name__}"}

def notion_append_blocks(page_id: str, content: str, *, timeout: float = None):
    """
    既存ページに本文を追加

    Args:
        page_id: 追加先ページID
        content: 追加する本文
        timeout: タイムアウト秒数

    Returns:
        dict: {"success": bool, "error": str}
    """
    if timeout is None:
        timeout = HTTP_TIMEOUT_SEC

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    # 本文ブロック
    children = []
    if content:
        max_len = 2000
        content_parts = [content[i:i+max_len] for i in range(0, len(content), max_len)]
        for part in content_parts:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": part}}]
                }
            })

    payload = {"children": children}

    try:
        resp = requests.patch(url, headers=_notion_headers(), data=json.dumps(payload), timeout=timeout)
        if resp.status_code != 200:
            error_msg = resp.json().get("message", "不明なエラー")
            return {"success": False, "error": f"API エラー: {error_msg}"}

        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": f"例外: {type(e).__name__}"}

def notion_add_to_database(title: str, content: str, *, database_id: str = None, timeout: float = None):
    """
    データベースに新しいエントリを追加

    Args:
        title: エントリタイトル（タイトルプロパティ）
        content: エントリ本文
        database_id: データベースID（省略時は環境変数のデフォルトDBを使用）
        timeout: タイムアウト秒数

    Returns:
        dict: {"success": bool, "page_id": str, "url": str, "error": str}
    """
    if timeout is None:
        timeout = HTTP_TIMEOUT_SEC

    if database_id is None:
        database_id = NOTION_DEFAULT_DATABASE_ID

    if not database_id:
        return {"success": False, "error": "データベースIDが指定されていません"}

    # まずデータベースのスキーマを取得して、タイトルプロパティ名を特定
    db_url = f"https://api.notion.com/v1/databases/{database_id}"
    try:
        db_resp = requests.get(db_url, headers=_notion_headers(), timeout=timeout)
        if db_resp.status_code != 200:
            return {"success": False, "error": "データベース情報の取得に失敗しました"}

        db_data = db_resp.json()
        db_properties = db_data.get("properties", {})

        # タイトルプロパティを探す
        title_property_name = None
        for prop_name, prop_data in db_properties.items():
            if prop_data.get("type") == "title":
                title_property_name = prop_name
                break

        if not title_property_name:
            return {"success": False, "error": "データベースにタイトルプロパティが見つかりません"}

    except Exception as e:
        return {"success": False, "error": f"データベース情報取得エラー: {type(e).__name__}"}

    url = "https://api.notion.com/v1/pages"

    # データベースエントリのプロパティ（動的に取得したプロパティ名を使用）
    properties = {
        title_property_name: {
            "title": [{"text": {"content": title}}]
        }
    }

    # 本文ブロック
    children = []
    if content:
        max_len = 2000
        content_parts = [content[i:i+max_len] for i in range(0, len(content), max_len)]
        for part in content_parts:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": part}}]
                }
            })

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": children
    }

    try:
        resp = requests.post(url, headers=_notion_headers(), data=json.dumps(payload), timeout=timeout)
        if resp.status_code != 200:
            error_msg = resp.json().get("message", "不明なエラー")
            return {"success": False, "error": f"API エラー: {error_msg}"}

        result = resp.json()
        return {
            "success": True,
            "page_id": result.get("id"),
            "url": result.get("url"),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": f"例外: {type(e).__name__}"}
