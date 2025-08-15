import http.client
import json
import os
import urllib.parse
import time
from dateutil import parser

# Настройки
RAPIDAPI_KEY = "427c7faa7bmshac7c567f35f2667p1e47d6jsn83598eb75717"   #os.getenv("RAPID_API_KEY")  # Убедись, что ключ установлен в переменных среды
if not RAPIDAPI_KEY or not isinstance(RAPIDAPI_KEY, str):
    raise ValueError("❌ RAPID_API_KEY не установлен или не является строкой.")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "stocktwits.p.rapidapi.com"
}
ANALYSIS_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "sentiment-analysis84.p.rapidapi.com"
}
SYMBOLS = ["AAPL", "MSFT", "TSLA"]
SAVE_PATH = "AITradingCrew"

def fetch_stocktwits_messages(symbol: str, limit: int = 30):
    conn = http.client.HTTPSConnection("stocktwits.p.rapidapi.com")
    endpoint = f"/streams/symbol/{symbol}.json?limit={limit}"
    conn.request("GET", endpoint, headers=HEADERS)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    try:
        json_data = json.loads(data)
        return json_data.get("messages", [])
    except Exception as e:
        print(f"❌ Ошибка при получении сообщений для {symbol}: {e}")
        return []

def analyze_sentiment(text: str):
    conn = http.client.HTTPSConnection("sentiment-analysis84.p.rapidapi.com")
    encoded_text = urllib.parse.quote(text)
    conn.request("GET", f"/analyse?text={encoded_text}", headers=ANALYSIS_HEADERS)
    res = conn.getresponse()
    try:
        data = json.loads(res.read().decode("utf-8"))
        pos = float(data.get("positive_probability", 0))
        neg = float(data.get("negative_probability", 0))
        if pos > 0.6:
            return "bullish"
        elif neg > 0.6:
            return "bearish"
        else:
            return "neutral"
    except Exception as e:
        print(f"⚠️ Ошибка анализа сентимента: {e}")
        return "neutral"

def process_symbol(symbol: str):
    print(f"🔍 Обработка {symbol}...")
    raw_messages = fetch_stocktwits_messages(symbol)
    analyzed = []

    for msg in raw_messages:
        body = msg.get("body", "").strip()
        if not body:
            continue
        sentiment = analyze_sentiment(body)
        timestamp = msg.get("created_at", "")
        try:
            dt = parser.parse(timestamp)
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        analyzed.append({
            "symbol": symbol,
            "timestamp": timestamp,
            "username": msg.get("user", {}).get("username", "Unknown"),
            "body": body,
            "sentiment": sentiment
        })
        time.sleep(1.2)  # уважение к API

    return analyzed

def save_result(data: dict):
    os.makedirs(SAVE_PATH, exist_ok=True)
    filepath = os.path.join(SAVE_PATH, "social_sentiment.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Сохранено в {filepath}")

if __name__ == "__main__":
    final_result = {}
    for symbol in SYMBOLS:
        final_result[symbol] = process_symbol(symbol)
    save_result(final_result)
