#!/usr/bin/env python3
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


DEFAULT_RSS_FEEDS = [
    "https://www.thaipbs.or.th/rss/news.xml",
    "https://www.bangkokpost.com/rss/data/topstories.xml",
    "https://www.nationthailand.com/rss",
]

DEFAULT_QUERIES = [
    "ข่าวไทยวันนี้",
    "ข่าวเศรษฐกิจไทยวันนี้",
    "หุ้นไทยวันนี้",
    "ราคาทองวันนี้",
    "ข่าวต่างประเทศวันนี้",
    "ข่าวคริปโตวันนี้",
]

DEFAULT_CATEGORIES = [
    "ข่าวด่วน",
    "ไทย",
    "การเมือง",
    "เศรษฐกิจ",
    "หุ้น",
    "ต่างประเทศ",
    "ทองคำ",
    "คริปโต",
    "เทคโนโลยี",
    "ธุรกิจ",
    "อสังหา",
    "พลังงาน",
    "กีฬา",
    "บันเทิง",
    "สุขภาพ",
    "ท่องเที่ยว",
    "สิ่งแวดล้อม",
]


def env_list(name, default_items):
    value = os.getenv(name, "").strip()
    if not value:
        return default_items
    return [item.strip() for item in value.split(",") if item.strip()]


def env_int(name, default_value):
    value = os.getenv(name, "").strip()
    if not value:
        return default_value
    try:
        return int(value)
    except ValueError:
        print(f"invalid_int_env name={name} value={value!r}; using {default_value}", file=sys.stderr)
        return default_value


def request_json(url, method="GET", payload=None, headers=None, timeout=25):
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def request_text(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "news-today-bot/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def stable_id(url, title):
    key = (url or title).strip().lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_rss_datetime(value):
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def extract_rss_items(feed_url):
    try:
        xml_text = request_text(feed_url)
        root = ET.fromstring(xml_text)
    except Exception as exc:
        print(f"rss_failed url={feed_url} error={exc}", file=sys.stderr)
        return []

    items = []
    for item in root.findall(".//item")[:20]:
        title = clean_text(item.findtext("title"))
        link = clean_text(item.findtext("link"))
        summary = clean_text(item.findtext("description"))
        published_at = parse_rss_datetime(item.findtext("pubDate"))
        if title and link:
            items.append(
                {
                    "id": stable_id(link, title),
                    "title": title,
                    "url": link,
                    "source": urllib.parse.urlparse(feed_url).netloc,
                    "raw_summary": summary[:900],
                    "published_at": published_at,
                    "provider": "rss",
                }
            )
    return items


def tavily_search(query):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    payload = {
        "query": query,
        "topic": "news",
        "search_depth": "basic",
        "max_results": 5,
        "include_answer": False,
    }
    try:
        result = request_json(
            "https://api.tavily.com/search",
            method="POST",
            payload=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
    except Exception as exc:
        print(f"tavily_failed query={query} error={exc}", file=sys.stderr)
        return []

    items = []
    for row in result.get("results", []):
        title = clean_text(row.get("title"))
        url = clean_text(row.get("url"))
        if not title or not url:
            continue
        items.append(
            {
                "id": stable_id(url, title),
                "title": title,
                "url": url,
                "source": urllib.parse.urlparse(url).netloc,
                "raw_summary": clean_text(row.get("content"))[:900],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "provider": "tavily",
            }
        )
    return items


def serpapi_search(query):
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []

    params = urllib.parse.urlencode(
        {
            "engine": "google_news",
            "q": query,
            "gl": "th",
            "hl": "th",
            "api_key": api_key,
        }
    )
    try:
        result = request_json(f"https://serpapi.com/search.json?{params}")
    except Exception as exc:
        print(f"serpapi_failed query={query} error={exc}", file=sys.stderr)
        return []

    items = []
    for row in result.get("news_results", [])[:5]:
        title = clean_text(row.get("title"))
        url = clean_text(row.get("link"))
        if not title or not url:
            continue
        source = row.get("source") or {}
        items.append(
            {
                "id": stable_id(url, title),
                "title": title,
                "url": url,
                "source": clean_text(source.get("name")) or urllib.parse.urlparse(url).netloc,
                "raw_summary": clean_text(row.get("snippet"))[:900],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "provider": "serpapi",
            }
        )
    return items


def classify_without_ai(item):
    text = f"{item['title']} {item.get('raw_summary', '')}".lower()
    rules = [
        ("หุ้น", ["หุ้น", "set", "ตลาดหลักทรัพย์", "ดัชนี"]),
        ("ทองคำ", ["ทอง", "gold"]),
        ("คริปโต", ["bitcoin", "crypto", "คริปโต", "บิตคอยน์"]),
        ("การเมือง", ["รัฐบาล", "ครม", "สภา", "นายก", "เลือกตั้ง"]),
        ("เศรษฐกิจ", ["เศรษฐกิจ", "ดอกเบี้ย", "เงินเฟ้อ", "เงินบาท", "gdp"]),
        ("ต่างประเทศ", ["สหรัฐ", "จีน", "ยุโรป", "ต่างประเทศ", "global"]),
        ("เทคโนโลยี", ["ai", "เทคโนโลยี", "ชิป", "semiconductor"]),
        ("พลังงาน", ["น้ำมัน", "พลังงาน", "ก๊าซ"]),
        ("กีฬา", ["ฟุตบอล", "กีฬา", "บอล"]),
        ("บันเทิง", ["บันเทิง", "คอนเสิร์ต", "ละคร"]),
        ("สุขภาพ", ["สุขภาพ", "โรงพยาบาล", "โรค"]),
        ("ท่องเที่ยว", ["ท่องเที่ยว", "โรงแรม", "นักท่องเที่ยว"]),
        ("สิ่งแวดล้อม", ["ฝุ่น", "อากาศ", "สิ่งแวดล้อม", "pm2.5"]),
    ]
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return category
    return "ไทย"


def summarize_with_gemini(item):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "summary": item.get("raw_summary") or item["title"],
            "category": classify_without_ai(item),
            "importance_score": 55,
        }

    model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "สรุปข่าวนี้เป็นภาษาไทยแบบอ่านง่าย และตอบกลับเป็น JSON เท่านั้น "
                            "schema: {\"summary\":\"string\",\"category\":\"one category\","
                            "\"importance_score\":number}. "
                            f"category ต้องเป็นหนึ่งใน {DEFAULT_CATEGORIES}. "
                            f"หัวข้อ: {item['title']}\n"
                            f"เนื้อหา: {item.get('raw_summary', '')}\n"
                            f"แหล่งข่าว: {item.get('source', '')}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"},
    }

    try:
        result = request_json(url, method="POST", payload=prompt)
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        category = parsed.get("category") if parsed.get("category") in DEFAULT_CATEGORIES else classify_without_ai(item)
        return {
            "summary": clean_text(parsed.get("summary"))[:600] or item.get("raw_summary") or item["title"],
            "category": category,
            "importance_score": int(parsed.get("importance_score") or 55),
        }
    except Exception as exc:
        print(f"gemini_failed title={item['title'][:60]} error={exc}", file=sys.stderr)
        return {
            "summary": item.get("raw_summary") or item["title"],
            "category": classify_without_ai(item),
            "importance_score": 50,
        }


def collect_news():
    items = []
    for feed in env_list("RSS_FEEDS", DEFAULT_RSS_FEEDS):
        items.extend(extract_rss_items(feed))
        time.sleep(0.2)

    for query in env_list("NEWS_SEARCH_QUERIES", DEFAULT_QUERIES):
        items.extend(tavily_search(query))
        items.extend(serpapi_search(query))
        time.sleep(0.2)

    deduped = {}
    for item in items:
        deduped[item["id"]] = item
    return list(deduped.values())


def save_to_supabase(items):
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        print("supabase_skipped missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    rows = []
    for item in items:
        rows.append(
            {
                "id": item["id"],
                "title": item["title"],
                "summary": item["summary"],
                "category": item["category"],
                "source": item["source"],
                "url": item["url"],
                "provider": item["provider"],
                "published_at": item["published_at"],
                "importance_score": item["importance_score"],
                "raw_summary": item.get("raw_summary", ""),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    endpoint = f"{supabase_url}/rest/v1/articles?on_conflict=id"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "resolution=merge-duplicates",
    }
    request_json(endpoint, method="POST", payload=rows, headers=headers)
    print(f"supabase_saved rows={len(rows)}")


def line_message(items):
    top_items = sorted(items, key=lambda row: row.get("importance_score", 0), reverse=True)[:3]
    if not top_items:
        return ""
    parts = ["ข่าวเด่นวันนี้"]
    for index, item in enumerate(top_items, start=1):
        parts.append(f"{index}. {item['title']}\nสรุป: {item['summary']}\nอ่านต่อ: {item['url']}")
    return "\n\n".join(parts)


def push_line(items):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to_ids = env_list("LINE_TO_IDS", [])
    if not token or not to_ids:
        print("line_skipped missing LINE_CHANNEL_ACCESS_TOKEN or LINE_TO_IDS")
        return

    text = line_message(items)
    if not text:
        print("line_skipped no top items")
        return

    headers = {"Authorization": f"Bearer {token}"}
    for to_id in to_ids:
        payload = {"to": to_id, "messages": [{"type": "text", "text": text[:4900]}]}
        request_json("https://api.line.me/v2/bot/message/push", method="POST", payload=payload, headers=headers)
        print(f"line_sent to={to_id}")


def main():
    items = collect_news()
    limit = env_int("MAX_ARTICLES_PER_RUN", 30)
    enriched = []
    for item in items[:limit]:
        ai = summarize_with_gemini(item)
        enriched.append({**item, **ai})
        time.sleep(0.25)

    save_to_supabase(enriched)

    if os.getenv("SEND_LINE_DIGEST", "false").lower() == "true":
        push_line(enriched)

    print(json.dumps({"collected": len(items), "processed": len(enriched)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
