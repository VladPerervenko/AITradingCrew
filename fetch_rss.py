import feedparser
import json
from datetime import datetime, timedelta
from dateutil import parser

RSS_FEEDS = {
    "AAPL": "https://finviz.com/rss.ashx?t=AAPL",
    "MSFT": "https://finviz.com/rss.ashx?t=MSFT",
    "NVDA": "https://finviz.com/rss.ashx?t=NVDA",
}

DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
CUTOFF_HOUR_UTC = 18

def get_cutoff():
    now_utc = datetime.utcnow()
    yesterday = now_utc - timedelta(days=1)
    cutoff = yesterday.replace(hour=CUTOFF_HOUR_UTC, minute=0, second=0, microsecond=0)
    return cutoff

def is_recent(entry_date: str, cutoff: datetime):
    try:
        published = parser.parse(entry_date)
        return published >= cutoff
    except Exception as e:
        print(f"⚠️ Ошибка даты: {entry_date} | {e}")
        return False

def fetch_and_filter_rss():
    cutoff = get_cutoff()
    result = {}

    for symbol, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        result[symbol] = []

        # Save raw entries for diagnostics
        with open(f"AITradingCrew/raw_feed_{symbol}.json", "w", encoding="utf-8") as f:
            json.dump(feed.entries, f, indent=2, ensure_ascii=False)

        for entry in feed.entries:
            entry_date = entry.get("published", "")
            if is_recent(entry_date, cutoff):
                result[symbol].append({
                "title": entry.title,
                "url": entry.link,
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "source": symbol
                })

        print(f"{symbol}: {len(result[symbol])} заголовков после фильтра по времени.")

    with open("AITradingCrew/filtered_rss_news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    fetch_and_filter_rss()