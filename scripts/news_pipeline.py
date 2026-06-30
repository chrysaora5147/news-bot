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
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "https://www.cnbc.com/id/19832390/device/rss/rss.html",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.ft.com/rss/home",
    "https://www.scmp.com/rss/91/feed",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "https://www.bangkokpost.com/rss/data/topstories.xml",
    "https://www.bangkokpost.com/rss/data/business.xml",
    "https://www.prachachat.net/feed",
    "https://thestandard.co/feed/",
    "https://www.infoquest.co.th/feed",
    "https://www.matichon.co.th/feed",
    "https://www.khaosod.co.th/feed",
    "https://www.thairath.co.th/rss/news",
    "https://www.kaohoon.com/feed",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.theguardian.com/football/rss",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.ballthai.com/feed/",
    "https://www.thairath.co.th/rss/sport",
    "https://www.khaosod.co.th/sports/feed",
]

DEFAULT_QUERIES = [
]

SPORTS_NEWS_QUERIES = [
    "ฟุตบอลโลก 2026 พลิกล็อก ผลบอล",
    "บอลโลก 2026 ผลการแข่งขันเมื่อคืน",
    "FIFA World Cup 2026 upset results",
    "World Cup 2026 Paraguay Germany Morocco Netherlands penalties",
]

DEFAULT_SUPABASE_URL = "https://zaqvrwsooxdtkepaaunk.supabase.co"
DEFAULT_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

DEFAULT_CATEGORIES = [
    "ข่าวด่วน",
    "ไทย",
    "เศรษฐกิจ",
    "หุ้น",
    "ทองคำ",
    "คริปโต",
    "เทคโนโลยี",
    "ธุรกิจ",
    "กีฬา",
]

WEB_MIN_IMPORTANCE_SCORE = 45
WEB_MIN_TRENDING_SCORE = 45
LINE_MIN_IMPORTANCE_SCORE = 60
LINE_MIN_TRENDING_SCORE = 78

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
    "fed",
    "inflation",
    "tariff",
    "trade",
    "war",
    "china",
    "us",
    "japan",
    "oil",
    "gold",
    "market",
    "earnings",
    "ai",
    "chip",
    "semiconductor",
    "ฟุตบอลโลก",
    "บอลโลก",
    "world cup",
    "fifa",
    "upset",
    "penalty",
    "penalties",
    "ผลบอล",
    "พลิกล็อก",
]

POLITICS_LINE_BLOCK_TERMS = [
    "รัฐบาล",
    "ครม",
    "นายก",
    "สภา",
    "รัฐมนตรี",
    "กระทรวง",
    "พรรค",
    "ฝ่ายค้าน",
    "เลือกตั้ง",
    "งบประมาณ",
    "งบจังหวัด",
    "ปรับลดงบ",
    "ชี้แจง",
    "แจง",
    "โต้",
    "ซัด",
    "อภิปราย",
    "ส.ส.",
    "สว.",
    "senate",
    "parliament",
    "minister",
    "government",
    "election",
    "trump",
    "putin",
]

CRIME_LINE_BLOCK_TERMS = [
    "ติดคุก",
    "จำคุก",
    "เรือนจำ",
    "ศาล",
    "คดี",
    "ฟ้อง",
    "จับกุม",
    "ฉ้อโกง",
    "ทุจริต",
    "ฆ่า",
    "ข่มขืน",
    "ล่วงละเมิด",
    "prison",
    "jail",
    "court",
    "fraud",
    "arrested",
    "sentenced",
]

MAJOR_INCIDENT_TERMS = [
    "แผ่นดินไหว",
    "สึนามิ",
    "เครื่องบินตก",
    "ไฟไหม้",
    "น้ำท่วม",
    "ถล่ม",
    "ระเบิด",
    "เสียชีวิต",
    "ผู้เสียชีวิต",
    "บาดเจ็บ",
    "earthquake",
    "tsunami",
    "crash",
    "flood",
    "explosion",
    "dead",
    "killed",
    "injured",
]

GENERIC_STORY_WORDS = {
    "news",
    "latest",
    "breaking",
    "live",
    "update",
    "updates",
    "analysis",
    "today",
    "says",
    "said",
    "after",
    "before",
    "over",
    "amid",
    "from",
    "with",
    "into",
    "about",
    "could",
    "would",
    "should",
    "will",
    "new",
    "top",
    "world",
    "market",
    "markets",
    "stock",
    "stocks",
    "shares",
    "ข่าว",
    "วันนี้",
    "ล่าสุด",
    "ด่วน",
    "สด",
    "อัปเดต",
    "อัพเดต",
    "ตลาด",
    "หุ้น",
    "ไทย",
}

LOW_QUALITY_PATTERNS = [
    "topicstoday",
    "topics today",
    "ห้องข่าว",
    "สุดสัปดาห์",
    "ดูดวง",
    "เลขเด็ด",
    "คลิป",
    "viral",
    "watch ",
    "full interview",
    "squawk box",
    "joins ",
    "morning bid",
    "newsletter",
    "live updates",
    "fifa55",
    "เว็บไซต์ทางการ",
    "official website",
    "เว็บไซต์อย่างเป็นทางการ",
    "เว็บพนัน",
    "เกมกีฬา",
    "ibd digital",
    "2 months for",
    "subscribe",
    "สมัครสมาชิก",
    "เข้าถึงได้ไม่จำกัด",
    "มีทีมนักข่าว",
    "appeared first",
    "เปิดเกมรุก",
    "ทุ่มงบการตลาด",
    "พรีเซ็นเตอร์",
    "โปรโมชั่น",
    "otop",
    "midyear",
    "งานแสดงสินค้า",
    "ขอบคุณประชาชนร่วมสนับสนุน",
    "ออกบูธ",
    "มหกรรม",
    "ลดราคา",
    "ดวง",
    "หวย",
    "ซุบซิบ",
]

BAD_SOURCE_PATTERNS = [
    "fifa55",
    "equiti",
    "investors.com",
    "skift.com",
]

SOURCE_QUALITY = {
    "bbc.co.uk": 28,
    "bbc.com": 28,
    "cnbc.com": 26,
    "aljazeera.com": 24,
    "wsj.com": 28,
    "ft.com": 28,
    "scmp.com": 22,
    "channelnewsasia.com": 22,
    "theguardian.com": 24,
    "espn.com": 22,
    "skysports.com": 18,
    "bangkokpost.com": 18,
    "infoquest.co.th": 20,
    "prachachat.net": 16,
    "thestandard.co": 16,
    "thaipbs.or.th": 18,
    "matichon.co.th": 15,
    "khaosod.co.th": 14,
    "thairath.co.th": 13,
    "kaohoon.com": 16,
    "ballthai.com": 13,
    "nationthailand.com": 13,
    "thaipost.net": 12,
    "naewna.com": 11,
    "reuters": 30,
    "bloomberg": 30,
    "associated press": 28,
    "ap news": 28,
    "nikkei": 24,
    "financial times": 28,
    "wall street journal": 28,
    "bbc": 28,
    "cnbc": 26,
}

THAI_MONTHS = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}


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
    value = value.replace('\\"', '"').replace("\\'", "'").replace("\\", "")
    return re.sub(r"\s+", " ", value).strip()


def strip_publisher_junk(value):
    value = clean_text(value)
    junk_patterns = [
        r"\bThe post\b.*$",
        r"\bappeared first\b.*$",
        r"\bRead more\b.*$",
        r"\bอ่านต่อ\b.*$",
        r"\s+ที่มา\s*:.*$",
        r"\s+\|\s+ห้องข่าว.*$",
        r"\s+\|\s+ข่าวหุ้นธุรกิจ.*$",
        r"\s+\|\s+.*ออนไลน์.*$",
    ]
    for pattern in junk_patterns:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE).strip()
    return value


def clean_fallback_title(value):
    value = strip_publisher_junk(value)
    value = re.sub(r"^[\"“”]+|[\"“”]+$", "", value).strip()
    value = re.sub(r"\s+\|\s+.*$", "", value)
    value = re.sub(r"\s+-\s+(ข่าวหุ้นธุรกิจ|HoonVision|Thai PBS|The Standard|Bangkok Post|ห้องข่าว).*$", "", value, flags=re.IGNORECASE)
    return value[:180]


def clean_fallback_summary(value, title=""):
    value = strip_publisher_junk(value)
    value = value.replace("[…]", " ").replace("…", " ")
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        value = clean_fallback_title(title)
    if value.startswith(title):
        value = value[len(title):].strip(" -:|")
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=บาท)\s+|(?<=แล้ว)\s+", value)
    summary = " ".join(sentence.strip() for sentence in sentences if sentence.strip())[:420]
    return summary or clean_fallback_title(title)


def contains_thai(value):
    return any("\u0e00" <= char <= "\u0e7f" for char in value or "")


def contains_term(text, term):
    term = term.lower()
    if re.fullmatch(r"[a-z0-9&.+'-]+(?:\s+[a-z0-9&.+'-]+)*", term):
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None
    return term in text


def contains_any_term(text, terms):
    return any(contains_term(text, term) for term in terms)


def text_for_decision(item):
    return f"{item.get('title', '')} {item.get('raw_summary', '')} {item.get('title_th', '')} {item.get('summary_th', '')} {item.get('category', '')}".lower()


def has_large_casualty_signal(text):
    if any(word in text for word in ["ร้อย", "พัน", "หมื่น", "แสน", "hundreds", "thousands"]):
        return contains_any_term(text, MAJOR_INCIDENT_TERMS)
    for number_text in re.findall(r"\d[\d,]*", text):
        try:
            number = int(number_text.replace(",", ""))
        except ValueError:
            continue
        if number >= 50 and contains_any_term(text, MAJOR_INCIDENT_TERMS):
            return True
    return False


def is_major_incident(item):
    text = text_for_decision(item)
    return contains_any_term(text, MAJOR_INCIDENT_TERMS) and has_large_casualty_signal(text)


def is_line_blocked_topic(item):
    text = text_for_decision(item)
    if is_major_incident(item):
        return False
    return contains_any_term(text, POLITICS_LINE_BLOCK_TERMS) or contains_any_term(text, CRIME_LINE_BLOCK_TERMS)


def is_line_worthy(item):
    if item.get("translation_fallback"):
        return False
    if not contains_thai(item.get("summary_th", "")):
        return False
    if is_low_quality_output(item) or is_line_blocked_topic(item):
        return False
    if item.get("category") in {"ทองคำ", "หุ้น", "เศรษฐกิจ", "คริปโต", "เทคโนโลยี", "ธุรกิจ", "กีฬา"}:
        return True
    return is_major_incident(item)


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
    value = re.sub(r"\b(reuters|bbc|cnbc|ft|scmp|al jazeera|channel news asia|bangkok post)\b", " ", value)
    value = re.sub(r"\b(today|latest|breaking|live|update|analysis)\b", " ", value)
    value = re.sub(r"\b(วันนี้|ล่าสุด|ด่วน|สด|วิเคราะห์|อัปเดต|อัพเดต)\b", " ", value)
    value = re.sub(r"[^\w\u0e00-\u0e7f]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def story_similarity(left, right):
    left_norm = normalize_story_text(left)
    right_norm = normalize_story_text(right)
    if not left_norm or not right_norm:
        return 0

    sequence_score = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = story_tokens(left_norm)
    right_tokens = story_tokens(right_norm)
    token_score = 0
    if left_tokens and right_tokens:
        token_score = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return max(sequence_score, token_score)


def story_tokens(value):
    return {
        token
        for token in value.split()
        if len(token) > 2 and token not in GENERIC_STORY_WORDS and not token.isdigit()
    }


def is_same_story(left, right):
    left_norm = normalize_story_text(left)
    right_norm = normalize_story_text(right)
    if not left_norm or not right_norm:
        return False

    sequence_score = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = story_tokens(left_norm)
    right_tokens = story_tokens(right_norm)
    common_tokens = left_tokens & right_tokens
    token_score = len(common_tokens) / len(left_tokens | right_tokens) if left_tokens and right_tokens else 0
    return sequence_score >= 0.82 or (token_score >= 0.45 and len(common_tokens) >= 2)


def normalize_category(category):
    if category in DEFAULT_CATEGORIES:
        return category
    if category in {"การเมือง", "ต่างประเทศ", "ข่าวต่างประเทศ"}:
        return "ไทย"
    if category in {"พลังงาน", "อสังหา"}:
        return "เศรษฐกิจ"
    if category in {"บันเทิง", "สุขภาพ", "ท่องเที่ยว", "สิ่งแวดล้อม"}:
        return "ไทย"
    return "ไทย"


def validated_category(item, requested_category=None):
    requested = normalize_category(requested_category or "")
    rule_category = classify_without_ai(item)
    text = f"{item.get('title', '')} {item.get('raw_summary', '')} {item.get('title_th', '')} {item.get('summary_th', '')}".lower()
    stock_terms = ["หุ้น", "set index", "set50", "set100", "sethd", "mai index", "ตลาดหลักทรัพย์", "ดัชนี", "delta", "nasdaq", "s&p", "dow jones"]
    business_terms = ["บริษัท", "ธุรกิจ", "ยอดขาย", "รายได้", "กำไร", "ลงทุน", "deal", "merger", "acquisition"]
    breaking_terms = ["attack", "attacks", "war", "missile", "dead", "killed", "gaza", "israel", "iran", "russia", "ukraine", "earthquake", "โจมตี", "สงคราม", "เสียชีวิต", "แผ่นดินไหว"]

    if requested == "หุ้น" and not contains_any_term(text, stock_terms):
        return rule_category
    if requested == "ธุรกิจ" and contains_any_term(text, breaking_terms):
        return "ข่าวด่วน"
    if requested == "ไทย" and is_foreign_source(item) and contains_any_term(text, breaking_terms):
        return "ข่าวด่วน"
    if requested == "ไทย" and is_foreign_source(item) and contains_any_term(text, business_terms):
        return "ธุรกิจ"
    return requested if requested in DEFAULT_CATEGORIES else rule_category


def source_key(item):
    source = item.get("source") or urllib.parse.urlparse(item.get("url", "")).netloc
    return source.lower().replace("www.", "").strip()


def is_foreign_source(item):
    source = source_key(item)
    return any(
        key in source
        for key in [
            "bbc",
            "cnbc",
            "aljazeera",
            "wsj",
            "ft",
            "scmp",
            "channelnewsasia",
            "reuters",
            "bloomberg",
            "forbes",
        ]
    )


def source_quality_score(item):
    haystack = f"{item.get('source', '')} {urllib.parse.urlparse(item.get('url', '')).netloc}".lower().replace("www.", "")
    return max((score for key, score in SOURCE_QUALITY.items() if key in haystack), default=6)


def item_image_url(item):
    for element in list(item):
        tag = element.tag.lower()
        if tag.endswith("enclosure") and (element.attrib.get("type", "").startswith("image") or element.attrib.get("url")):
            return clean_text(element.attrib.get("url"))
        if tag.endswith("content") or tag.endswith("thumbnail"):
            url = clean_text(element.attrib.get("url"))
            if url:
                return url
    description = item.findtext("description") or ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description, flags=re.IGNORECASE)
    return clean_text(match.group(1)) if match else ""


def page_og_image(url):
    try:
        text = request_text(url, timeout=10)[:200000]
    except Exception:
        return ""
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return urllib.parse.urljoin(url, html.unescape(match.group(1)))
    return ""


def is_low_quality_story(item):
    text = f"{item.get('title', '')} {item.get('raw_summary', '')} {item.get('source', '')} {item.get('url', '')}".lower()
    return any(pattern in text for pattern in LOW_QUALITY_PATTERNS + BAD_SOURCE_PATTERNS)


def is_low_quality_output(item):
    text = f"{item.get('title_th', '')} {item.get('summary_th', '')} {item.get('source', '')} {item.get('url', '')}".lower()
    return any(pattern in text for pattern in LOW_QUALITY_PATTERNS + BAD_SOURCE_PATTERNS)


def passes_source_gate(item):
    return source_quality_score(item) >= 16 or item.get("source_count", 1) >= 2


def passes_web_source_gate(item):
    return source_quality_score(item) >= 12 or item.get("source_count", 1) >= 2


def acceptable_fallback(item):
    original_text = f"{item.get('title', '')} {item.get('raw_summary', '')}"
    return (
        item.get("translation_fallback")
        and contains_thai(original_text)
        and item.get("image_url")
        and item.get("source_count", 1) >= 2
        and not is_low_quality_story(item)
    )


def acceptable_web_fallback(item):
    original_text = f"{item.get('title', '')} {item.get('raw_summary', '')}"
    output_text = f"{item.get('title_th', '')} {item.get('summary_th', '')}"
    return (
        item.get("translation_fallback")
        and contains_thai(output_text)
        and not is_low_quality_story(item)
        and not is_low_quality_output(item)
        and (
            source_quality_score(item) >= 20
            or item.get("source_count", 1) >= 2
            or (contains_thai(original_text) and source_quality_score(item) >= 12)
        )
    )


def is_stale_dated_story(item):
    text = f"{item.get('title', '')} {item.get('raw_summary', '')}"
    now = datetime.now(timezone(timedelta(hours=7))).date()
    for day, month_name in re.findall(r"(\d{1,2})\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)", text):
        try:
            story_date = datetime(now.year, THAI_MONTHS[month_name], int(day)).date()
        except ValueError:
            continue
        if abs((now - story_date).days) > 1:
            return True
    return False


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
        source_name = clean_text(item.findtext("source")) or urllib.parse.urlparse(feed_url).netloc
        published_at = parse_rss_datetime(item.findtext("pubDate"))
        if title and link:
            items.append(
                {
                    "id": stable_id(link, title),
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "raw_summary": clean_fallback_summary(summary, title)[:900],
                    "image_url": item_image_url(item),
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
            if is_same_story(item["title"], cluster["title"]):
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
                urls.append({"title": clean_fallback_title(row["title"]), "url": row["url"], "source": row.get("source", "")})
                seen_urls.add(row["url"])

        merged_summary = " ".join(
            clean_text(row.get("raw_summary") or row["title"]) for row in cluster_items[:5]
        )[:1800]
        story = {
            **representative,
            "id": story_id_from_title(cluster["title"]),
            "story_id": story_id_from_title(cluster["title"]),
            "title": clean_fallback_title(representative["title"]),
            "raw_summary": merged_summary or representative.get("raw_summary", ""),
            "image_url": representative.get("image_url", "") or next((row.get("image_url", "") for row in cluster_items if row.get("image_url")), ""),
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
    if is_low_quality_story(item) or is_stale_dated_story(item):
        return 20
    source_boost = min(item.get("source_count", 1), 5) * 8
    quality_boost = source_quality_score(item)
    keyword_boost = sum(5 for keyword in TRENDING_KEYWORDS if keyword in text)
    provider_boost = 8 if "+" in item.get("provider", "") else 0
    freshness_boost = 0
    try:
        published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        age_hours = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
        freshness_boost = max(0, 24 - int(age_hours))
    except Exception:
        freshness_boost = 8
    return 22 + quality_boost + source_boost + keyword_boost + provider_boost + freshness_boost


def final_trending_score(item):
    base = int(item.get("importance_score", 50))
    source_boost = min(item.get("source_count", 1), 5) * 6
    quality_boost = int(source_quality_score(item) * 0.7)
    keyword_boost = min(12, sum(3 for keyword in TRENDING_KEYWORDS if keyword in f"{item['title']} {item.get('summary_th', '')}".lower()))
    freshness_boost = 0
    try:
        published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        age_hours = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
        freshness_boost = max(0, 12 - int(age_hours))
    except Exception:
        freshness_boost = 5
    provider_boost = 4 if "+" in item.get("provider", "") else 0
    translated_penalty = -8 if item.get("translation_fallback") else 0
    return min(92, int(base * 0.72) + quality_boost + source_boost + keyword_boost + freshness_boost + provider_boost + translated_penalty)


def fallback_importance_score(item, translated=False):
    text = f"{item.get('title', '')} {item.get('raw_summary', '')}"
    if is_low_quality_story(item) or is_stale_dated_story(item):
        return 40
    if not contains_thai(text) and not translated:
        return 40
    floor = 60 if translated and source_quality_score(item) >= 20 else 55
    ceiling = 76 if translated else 78
    return min(ceiling, max(floor, pre_ai_story_score(item) - 18))


def translate_text_th(value):
    value = clean_text(value)[:900]
    if not value or contains_thai(value):
        return value
    params = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "auto",
            "tl": "th",
            "dt": "t",
            "q": value,
        }
    )
    try:
        result = request_json(f"https://translate.googleapis.com/translate_a/single?{params}", timeout=15)
        translated = "".join(part[0] for part in result[0] if part and part[0])
        return clean_text(translated)
    except Exception as exc:
        print(f"translate_failed title={value[:60]} error={exc}", file=sys.stderr)
        return ""


def translated_fallback(item):
    title_th = translate_text_th(clean_fallback_title(item["title"]))
    summary_source = clean_fallback_summary(item.get("raw_summary"), item["title"])
    summary_th = translate_text_th(summary_source)
    translated = contains_thai(title_th) and contains_thai(summary_th)
    return {
        "title_th": title_th or clean_fallback_title(item["title"]),
        "summary": summary_th or summary_source,
        "summary_th": summary_th or summary_source,
        "category": validated_category(item, classify_without_ai(item)),
        "importance_score": fallback_importance_score(item, translated=translated),
        "translation_fallback": True,
    }


def google_news_rss_search(query, hl="en-US", gl="US", ceid="US:en"):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    return [{**item, "provider": "google_news"} for item in extract_rss_items(url)[:12]]


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
                "raw_summary": clean_fallback_summary(row.get("content"), title)[:900],
                "image_url": "",
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
                "raw_summary": clean_fallback_summary(row.get("snippet"), title)[:900],
                "image_url": clean_text(row.get("thumbnail")),
                "published_at": datetime.now(timezone.utc).isoformat(),
                "provider": "serpapi",
            }
        )
    return items


def classify_without_ai(item):
    text = f"{item['title']} {item.get('raw_summary', '')}".lower()
    rules = [
        ("หุ้น", ["หุ้น", "set index", "set50", "set100", "sethd", "mai index", "ตลาดหลักทรัพย์", "ดัชนี"]),
        ("ทองคำ", ["ทอง", "gold"]),
        ("คริปโต", ["bitcoin", "crypto", "คริปโต", "บิตคอยน์"]),
        ("ข่าวด่วน", ["attack", "attacks", "war", "missile", "dead", "killed", "gaza", "israel", "iran", "russia", "ukraine", "earthquake", "โจมตี", "สงคราม", "เสียชีวิต", "แผ่นดินไหว"]),
        ("ไทย", ["รัฐบาล", "ครม", "สภา", "นายก", "เลือกตั้ง"]),
        ("เศรษฐกิจ", ["เศรษฐกิจ", "ดอกเบี้ย", "เงินเฟ้อ", "เงินบาท", "เงินเยน", "ค่าเงิน", "gdp", "fed", "federal reserve", "central bank", "inflation", "yen", "currency", "factory", "manufacturing", "tariff", "trade"]),
        ("ไทย", ["สหรัฐ", "จีน", "ยุโรป", "ต่างประเทศ", "global", "trump", "china"]),
        ("เทคโนโลยี", ["ai", "เทคโนโลยี", "ชิป", "semiconductor"]),
        ("เศรษฐกิจ", ["น้ำมัน", "พลังงาน", "ก๊าซ"]),
        ("กีฬา", ["ฟุตบอล", "กีฬา", "บอล", "บอลโลก", "ฟุตบอลโลก", "world cup", "fifa", "penalty", "penalties", "ผลบอล", "พลิกล็อก", "paraguay", "germany", "morocco", "netherlands"]),
        ("ธุรกิจ", ["บริษัท", "ธุรกิจ", "ยอดขาย", "รายได้", "กำไร", "ลงทุน"]),
    ]
    for category, keywords in rules:
        if contains_any_term(text, keywords):
            return normalize_category(category)
    return "ไทย"


def gemini_models():
    configured = os.getenv("GEMINI_MODEL", "").strip()
    if configured:
        return [configured] + [model for model in DEFAULT_GEMINI_MODELS if model != configured]
    return DEFAULT_GEMINI_MODELS


def summarize_with_gemini(item):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return translated_fallback(item)

    prompt = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "อ่านข่าวนี้แล้วแปล/เขียนให้อยู่ในภาษาไทยธรรมชาติสำหรับคนไทย "
                            "แม้ต้นฉบับเป็นภาษาอังกฤษหรือภาษาอื่น ให้สรุปออกมาเป็นภาษาไทยทั้งหมด "
                            "ตอบกลับเป็น JSON เท่านั้น ห้ามมี markdown หรือคำอธิบายเพิ่ม "
                            "schema: {\"title_th\":\"string\",\"summary_th\":\"string\","
                            "\"category\":\"one category\",\"importance_score\":number}. "
                            "title_th ต้องเป็นหัวข้อข่าวภาษาไทยที่บอกสาระสำคัญ ไม่ใช่หัวข้อ SEO หรือชื่อรายการ "
                            "summary_th ต้องเป็นสรุปภาษาไทย 1-2 ประโยค บอกว่าเกิดอะไรขึ้น ทำไมสำคัญ และกระทบใคร ไม่เกิน 450 ตัวอักษร "
                            f"category ต้องเป็นหนึ่งใน {DEFAULT_CATEGORIES}. "
                            "importance_score ให้ 0-100 เฉพาะข่าวที่มีผลต่อเศรษฐกิจ ตลาด การเมือง เทคโนโลยี ภูมิรัฐศาสตร์ "
                            "กีฬาใหญ่ระดับโลก เช่น ฟุตบอลโลก ผลการแข่งขันพลิกล็อก หรือแมตช์สำคัญ "
                            "หรือเป็นเหตุการณ์ใหญ่ระดับประเทศ/โลกเท่านั้นจึงควรเกิน 70 "
                            "ข่าว advertorial, โปรโมชัน, ไวรัล, รายการวิดีโอ, gossip หรือเรื่องเล็กมากให้ต่ำกว่า 50 "
                            f"หัวข้อ: {item['title']}\n"
                            f"เนื้อหา: {item.get('raw_summary', '')}\n"
                            f"แหล่งข่าว: {item.get('source', '')}\n"
                            f"จำนวนแหล่งข่าวใน story: {item.get('source_count', 1)}"
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
            category = validated_category(item, parsed.get("category") or classify_without_ai(item))
            summary_th = clean_text(parsed.get("summary_th") or parsed.get("summary"))[:600]
            title_th = clean_text(parsed.get("title_th"))[:220]
            importance_score = int(parsed.get("importance_score") or 55)
            if not contains_thai(summary_th):
                importance_score = min(importance_score, 40)
            output = {"title_th": title_th, "summary_th": summary_th, **item}
            if is_low_quality_story(item) or is_low_quality_output(output) or is_stale_dated_story(item):
                importance_score = min(importance_score, 45)
            return {
                "title_th": title_th or item["title"],
                "summary": summary_th or item.get("raw_summary") or item["title"],
                "summary_th": summary_th or item.get("raw_summary") or item["title"],
                "category": validated_category({**item, "title_th": title_th, "summary_th": summary_th}, category),
                "importance_score": importance_score,
            }
        except Exception as exc:
            print(f"gemini_failed model={model} title={item['title'][:60]} error={exc}", file=sys.stderr)

    print(f"gemini_all_models_failed title={item['title'][:60]}", file=sys.stderr)
    return translated_fallback(item)


def collect_news():
    items = []
    configured_feeds = env_list("RSS_FEEDS", [])
    feeds = DEFAULT_RSS_FEEDS + [feed for feed in configured_feeds if feed not in DEFAULT_RSS_FEEDS]
    for feed in feeds:
        items.extend(extract_rss_items(feed))
        time.sleep(0.2)

    for query in SPORTS_NEWS_QUERIES:
        items.extend(google_news_rss_search(query, hl="th", gl="TH", ceid="TH:th")[:8])
        time.sleep(0.2)

    for query in env_list("NEWS_SEARCH_QUERIES", DEFAULT_QUERIES):
        if os.getenv("ENABLE_SEARCH_PROVIDERS", "false").lower() == "true":
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
        if (
            item["importance_score"] < WEB_MIN_IMPORTANCE_SCORE
            or item.get("trending_score", 0) < WEB_MIN_TRENDING_SCORE
            or is_low_quality_output(item)
            or not passes_web_source_gate(item)
            or (item.get("translation_fallback") and not acceptable_web_fallback(item))
        ):
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
                "image_url": item.get("image_url", ""),
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
    limit = max(30, env_int("MAX_ARTICLES_PER_RUN", 30))
    enriched = []
    for item in items[:limit]:
        if not item.get("image_url"):
            item["image_url"] = page_og_image(item["url"])
        ai = summarize_with_gemini(item)
        row = {**item, **ai}
        row["trending_score"] = final_trending_score(row)
        if acceptable_fallback(row):
            row["importance_score"] = max(row.get("importance_score", 0), 62)
            row["trending_score"] = max(row.get("trending_score", 0), 70)
        if is_low_quality_output(row) or not passes_source_gate(row):
            row["importance_score"] = min(row["importance_score"], 45)
            row["trending_score"] = min(row["trending_score"], 45)
        if (row.get("translation_fallback") and not acceptable_fallback(row)) or not row.get("image_url"):
            row["importance_score"] = min(row["importance_score"], 55)
            row["trending_score"] = min(row["trending_score"], 55)
        row["line_candidate"] = (
            row.get("trending_score", 0) >= LINE_MIN_TRENDING_SCORE
            and row.get("importance_score", 0) >= LINE_MIN_IMPORTANCE_SCORE
            and is_line_worthy(row)
        )
        enriched.append(row)
        time.sleep(0.25)

    save_to_supabase(enriched)

    if os.getenv("SEND_LINE_DIGEST", "false").lower() == "true":
        push_line(enriched)

    print(json.dumps({"collected": len(items), "processed": len(enriched)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
