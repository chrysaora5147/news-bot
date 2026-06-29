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
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher


DEFAULT_RSS_FEEDS = [
    "https://www.bangkokpost.com/rss/data/topstories.xml",
    "https://www.bangkokpost.com/rss/data/business.xml",
    "https://www.thairath.co.th/rss/news",
    "https://www.thairath.co.th/rss/business",
    "https://www.matichon.co.th/feed",
    "https://www.khaosod.co.th/feed",
    "https://www.prachachat.net/feed",
    "https://www.thaipost.net/feed/",
    "https://thestandard.co/feed/",
    "https://workpointtoday.com/feed/",
    "https://www.infoquest.co.th/feed",
    "https://www.kaohoon.com/feed",
]

DEFAULT_QUERIES = [
    "ข่าวไทยวันนี้",
    "ข่าวด่วนวันนี้",
    "ข่าวการเมืองไทยล่าสุด",
    "ข่าวเศรษฐกิจไทยวันนี้",
    "หุ้นไทยวันนี้",
    "ข่าว SET วันนี้",
    "ราคาทองวันนี้",
    "ข่าวคริปโตวันนี้",
    "ข่าวต่างประเทศวันนี้",
    "ข่าวธุรกิจไทยวันนี้",
    "ข่าวพลังงาน น้ำมัน วันนี้",
    "ข่าวอสังหา วันนี้",
]

DEFAULT_SUPABASE_URL = "https://zaqvrwsooxdtkepaaunk.supabase.co"
DEFAULT_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

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

TRENDING_KEYWORDS = [
    "ด่วน",
    "ล่าสุด",
    "ครม",
    "รัฐบาล",
    "นายก",
    "สภา",
    "งบประมาณ",
    "เศรษฐกิจ",
    "เงินเฟ้อ",
    "ดอกเบี้ย",
    "บาท",
    "หุ้น",
    "set",
    "ตลาดหลักทรัพย์",
    "ทอง",
    "น้ำมัน",
    "พลังงาน",
    "สงคราม",
    "เลือกตั้ง",
    "ภาษี",
    "ธปท",
    "กนง",
    "ส่งออก",
    "นักลงทุน",
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


def normalize_supabase_url(value):
    value = (value or "").strip()
    if not value:
        return DEFAULT_SUPABASE_URL
    if value.startswith("http"):
        parsed = urllib.parse.urlparse(value)
        if parsed.netloc.endswith(".supabase.co"):
            return f"{parsed.scheme}://{parsed.netloc}"
        match = re.search(r"/project/([a-z0-9]{20})", parsed.path)
        if match:
            return f"https://{match.group(1)}.supabase.co"
        return DEFAULT_SUPABASE_URL
    if re.fullmatch(r"[a-z0-9]{20}", value):
        return f"https://{value}.supabase.co"
    return DEFAULT_SUPABASE_URL


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


def is_rate_limited(exc):
    return getattr(exc, "code", None) == 429


def request_text(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "news-today-bot/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_xml_text(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value or "")


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def clean_fallback_title(value):
    value = clean_text(value)
    value = re.sub(r"\s+\|\s+.*$", "", value)
    value = re.sub(r"\s+-\s+[A-Za-zก-๙].*$", "", value)
    return value[:180]


def contains_thai(value):
    return any("\u0e00" <= char <= "\u0e7f" for char in value or "")


def stable_id(url, title):
    key = (url or title).strip().lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def story_id_from_title(title):
    normalized = normalize_story_text(title)
    return "story_" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def normalize_story_text(value):
    value = clean_text(value).lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[-|:–—].*$", " ", value)
    value = re.sub(r"[^\w\u0e00-\u0e7f]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def story_similarity(left, right):
    left_norm = normalize_story_text(left)
    right_norm = normalize_story_text(right)
    if not left_norm or not right_norm:
        return 0

    sequence_score = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = {token for token in left_norm.split() if len(token) > 2}
    right_tokens = {token for token in right_norm.split() if len(token) > 2}
    token_score = 0
    if left_tokens and right_tokens:
        token_score = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return max(sequence_score, token_score)


def source_key(item):
    source = item.get("source") or urllib.parse.urlparse(item.get("url", "")).netloc
    return source.lower().replace("www.", "").strip()


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
        xml_text = clean_xml_text(request_text(feed_url))
        root = ET.fromstring(xml_text)
    except Exception as exc:
        print(f"rss_failed url={feed_url} error={exc}", file=sys.stderr)
        return []

    items = []
    for item in root.findall(".//item")[:30]:
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


def cluster_news(items):
    sorted_items = sorted(items, key=lambda item: item.get("published_at", ""), reverse=True)
    clusters = []
    for item in sorted_items:
        matched = None
        for cluster in clusters:
            if story_similarity(item["title"], cluster["title"]) >= 0.62:
                matched = cluster
                break
        if matched:
            matched["items"].append(item)
            matched["title"] = max([row["title"] for row in matched["items"]], key=len)
        else:
            clusters.append({"title": item["title"], "items": [item]})

    stories = []
    for cluster in clusters:
        cluster_items = cluster["items"]
        representative = max(
            cluster_items,
            key=lambda row: (len(row.get("raw_summary", "")), row.get("published_at", "")),
        )
        sources = sorted({source_key(row) for row in cluster_items if source_key(row)})
        urls = []
        seen_urls = set()
        for row in cluster_items:
            if row["url"] not in seen_urls:
                urls.append({"title": row["title"], "url": row["url"], "source": row.get("source", "")})
                seen_urls.add(row["url"])

        merged_summary = " ".join(
            clean_text(row.get("raw_summary") or row["title"]) for row in cluster_items[:5]
        )[:1800]
        story = {
            **representative,
            "id": story_id_from_title(cluster["title"]),
            "story_id": story_id_from_title(cluster["title"]),
            "title": representative["title"],
            "raw_summary": merged_summary or representative.get("raw_summary", ""),
            "source": ", ".join(sources[:4]) or representative.get("source", ""),
            "source_count": max(1, len(sources)),
            "source_urls": urls[:8],
            "provider": "+".join(sorted({row.get("provider", "unknown") for row in cluster_items}))[:80],
            "published_at": max(row.get("published_at", representative["published_at"]) for row in cluster_items),
        }
        stories.append(story)

    return sorted(stories, key=pre_ai_story_score, reverse=True)


def pre_ai_story_score(item):
    text = f"{item['title']} {item.get('raw_summary', '')}".lower()
    source_boost = min(item.get("source_count", 1), 5) * 10
    keyword_boost = sum(5 for keyword in TRENDING_KEYWORDS if keyword in text)
    provider_boost = 8 if "+" in item.get("provider", "") else 0
    freshness_boost = 0
    try:
        published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        age_hours = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
        freshness_boost = max(0, 24 - int(age_hours))
    except Exception:
        freshness_boost = 8
    return 35 + source_boost + keyword_boost + provider_boost + freshness_boost


def final_trending_score(item):
    base = int(item.get("importance_score", 50))
    source_boost = min(item.get("source_count", 1), 5) * 6
    keyword_boost = min(12, sum(3 for keyword in TRENDING_KEYWORDS if keyword in f"{item['title']} {item.get('summary_th', '')}".lower()))
    freshness_boost = 0
    try:
        published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        age_hours = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
        freshness_boost = max(0, 12 - int(age_hours))
    except Exception:
        freshness_boost = 5
    provider_boost = 4 if "+" in item.get("provider", "") else 0
    return min(100, int(base * 0.78) + source_boost + keyword_boost + freshness_boost + provider_boost)


def fallback_importance_score(item):
    text = f"{item.get('title', '')} {item.get('raw_summary', '')}"
    if not contains_thai(text):
        return 40
    return min(78, max(55, pre_ai_story_score(item) - 15))


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


def gemini_models():
    configured = os.getenv("GEMINI_MODEL", "").strip()
    if configured:
        return [configured] + [model for model in DEFAULT_GEMINI_MODELS if model != configured]
    return DEFAULT_GEMINI_MODELS


def summarize_with_gemini(item):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        fallback_text = item.get("raw_summary") or item["title"]
        return {
            "title_th": clean_fallback_title(item["title"]),
            "summary": fallback_text,
            "summary_th": fallback_text,
            "category": classify_without_ai(item),
            "importance_score": fallback_importance_score(item),
        }

    prompt = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "อ่านข่าวนี้แล้วแปล/เขียนให้อยู่ในภาษาไทยธรรมชาติสำหรับคนไทย "
                            "ตอบกลับเป็น JSON เท่านั้น ห้ามมี markdown หรือคำอธิบายเพิ่ม "
                            "schema: {\"title_th\":\"string\",\"summary_th\":\"string\","
                            "\"category\":\"one category\",\"importance_score\":number}. "
                            "title_th ต้องเป็นหัวข้อข่าวภาษาไทยที่สั้น ชัด และไม่แต่งข้อมูลเพิ่ม "
                            "summary_th ต้องเป็นสรุปภาษาไทย 1-2 ประโยค อ่านง่าย ไม่เกิน 450 ตัวอักษร "
                            f"category ต้องเป็นหนึ่งใน {DEFAULT_CATEGORIES}. "
                            "importance_score ให้ 0-100 โดยคัดเฉพาะข่าวสำคัญจริงให้คะแนนสูง "
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

    for model in gemini_models():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            result = request_json(url, method="POST", payload=prompt)
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            category = parsed.get("category") if parsed.get("category") in DEFAULT_CATEGORIES else classify_without_ai(item)
            summary_th = clean_text(parsed.get("summary_th") or parsed.get("summary"))[:600]
            title_th = clean_text(parsed.get("title_th"))[:220]
            importance_score = int(parsed.get("importance_score") or 55)
            if not contains_thai(summary_th):
                importance_score = min(importance_score, 40)
            return {
                "title_th": title_th or item["title"],
                "summary": summary_th or item.get("raw_summary") or item["title"],
                "summary_th": summary_th or item.get("raw_summary") or item["title"],
                "category": category,
                "importance_score": importance_score,
            }
        except Exception as exc:
            print(f"gemini_failed model={model} title={item['title'][:60]} error={exc}", file=sys.stderr)
            if is_rate_limited(exc):
                break

    print(f"gemini_all_models_failed title={item['title'][:60]}", file=sys.stderr)
    fallback_text = item.get("raw_summary") or item["title"]
    return {
        "title_th": clean_fallback_title(item["title"]),
        "summary": fallback_text,
        "summary_th": fallback_text,
        "category": classify_without_ai(item),
        "importance_score": fallback_importance_score(item),
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
    return cluster_news(list(deduped.values()))


def save_to_supabase(items):
    supabase_url = normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        print("supabase_skipped missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    rows = []
    for item in items:
        if item["importance_score"] < 50:
            continue
        rows.append(
            {
                "id": item["id"],
                "story_id": item.get("story_id") or item["id"],
                "title": item["title"],
                "title_th": item.get("title_th") or item["title"],
                "summary": item["summary"],
                "summary_th": item.get("summary_th") or item["summary"],
                "category": item["category"],
                "source": item["source"],
                "source_count": item.get("source_count", 1),
                "source_urls": item.get("source_urls", []),
                "url": item["url"],
                "provider": item["provider"],
                "published_at": item["published_at"],
                "importance_score": item["importance_score"],
                "trending_score": item.get("trending_score", item["importance_score"]),
                "line_candidate": item.get("line_candidate", False),
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
    if not rows:
        print("supabase_skipped no rows above importance threshold")
        return
    request_json(endpoint, method="POST", payload=rows, headers=headers)
    print(f"supabase_saved rows={len(rows)}")


def get_line_sent_ids(items):
    supabase_url = normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    ids = [item["id"] for item in items if item.get("id")]
    if not supabase_url or not service_key or not ids:
        return set()

    safe_ids = ",".join(ids[:50])
    endpoint = f"{supabase_url}/rest/v1/articles?select=id,line_sent_at&id=in.({safe_ids})"
    headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
    try:
        rows = request_json(endpoint, headers=headers)
    except Exception as exc:
        print(f"line_sent_lookup_failed error={exc}", file=sys.stderr)
        return set()
    return {row["id"] for row in rows if row.get("line_sent_at")}


def mark_line_sent(items):
    supabase_url = normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    ids = [item["id"] for item in items if item.get("id")]
    if not supabase_url or not service_key or not ids:
        return

    safe_ids = ",".join(ids[:50])
    endpoint = f"{supabase_url}/rest/v1/articles?id=in.({safe_ids})"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "return=minimal",
    }
    request_json(
        endpoint,
        method="PATCH",
        payload={"line_sent_at": datetime.now(timezone.utc).isoformat()},
        headers=headers,
    )


def line_message(items):
    sent_ids = get_line_sent_ids(items)
    top_items = sorted(
        [
            item
            for item in items
            if item.get("line_candidate") and item.get("id") not in sent_ids
        ],
        key=lambda row: (row.get("trending_score", 0), row.get("importance_score", 0), row.get("source_count", 1)),
        reverse=True,
    )[:3]
    if not top_items:
        return "", []
    parts = ["ข่าวเด่นวันนี้"]
    for index, item in enumerate(top_items, start=1):
        title = item.get("title_th") or item["title"]
        summary = item.get("summary_th") or item["summary"]
        source_count = item.get("source_count", 1)
        parts.append(
            f"{index}. {title}\n"
            f"สรุป: {summary}\n"
            f"ความดัง: {item.get('trending_score', item.get('importance_score', 0))}/100 | {source_count} แหล่งข่าว\n"
            f"อ่านต่อ: {item['url']}"
        )
    return "\n\n".join(parts), top_items


def push_line(items):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to_ids = env_list("LINE_TO_IDS", [])
    if not token or not to_ids:
        print("line_skipped missing LINE_CHANNEL_ACCESS_TOKEN or LINE_TO_IDS")
        return

    text, sent_items = line_message(items)
    if not text:
        print("line_skipped no top items")
        return

    headers = {"Authorization": f"Bearer {token}"}
    for to_id in to_ids:
        payload = {"to": to_id, "messages": [{"type": "text", "text": text[:4900]}]}
        request_json("https://api.line.me/v2/bot/message/push", method="POST", payload=payload, headers=headers)
        print(f"line_sent to={to_id}")
    mark_line_sent(sent_items)


def main():
    items = collect_news()
    limit = env_int("MAX_ARTICLES_PER_RUN", 18)
    enriched = []
    for item in items[:limit]:
        ai = summarize_with_gemini(item)
        row = {**item, **ai}
        row["trending_score"] = final_trending_score(row)
        row["line_candidate"] = (
            row.get("trending_score", 0) >= 78
            and row.get("importance_score", 0) >= 60
            and contains_thai(row.get("summary_th", ""))
        )
        enriched.append(row)
        time.sleep(0.25)

    save_to_supabase(enriched)

    if os.getenv("SEND_LINE_DIGEST", "false").lower() == "true":
        push_line(enriched)

    print(json.dumps({"collected": len(items), "processed": len(enriched)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
