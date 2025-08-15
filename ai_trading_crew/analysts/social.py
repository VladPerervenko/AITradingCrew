import os
import json
import datetime
import pytz
import http.client


def fetch_stocktwits_messages(symbol : str, desired_count : int, lower_bound : datetime):
    messages = []
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    empty_count = 0
    pagination_max = None
    #conn = http.client.HTTPSConnection("stocktwits.p.rapidapi.com")
    conn = http.client.HTTPSConnection("twitter241.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': os.getenv("RAPID_API_KEY"),
        'x-rapidapi-host': "twitter241.p.rapidapi.com" #'x-rapidapi-host': "stocktwits.p.rapidapi.com"
    }
    
    while len(messages) < desired_count:
        endpoint = f"/streams/symbol/{symbol}.json?limit={desired_count}"
        if pagination_max:
            endpoint += f"&max={pagination_max}"
        conn.request("GET", endpoint, headers=headers)
        #conn.request("GET", "/community-details?communityId=1601841656147345410", headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        try:
            json_data = json.loads(data)
        except Exception as e:
            print("Error decoding StockTwits API response:", e) # Changed message for clarity
            break
        
        page_msgs = json_data.get("messages", [])
        if not page_msgs:
            break
        
        stop = False
        for msg in page_msgs:
            created_at_str = msg.get("created_at")
            if not created_at_str:
                continue
            dt = datetime.datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
            tz_est = pytz.timezone("US/Eastern")
            dt = pytz.utc.localize(dt).astimezone(tz_est)
            if dt < lower_bound:
                stop = True
                break
            body = msg.get("body", "").strip()
            username = msg.get("user", {}).get("username", "Unknown")
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            # Вместо добавления форматированной строки сразу, сохраним в виде словаря или более структурированно
            # чтобы потом собрать в JSON
            message_obj = {
                "timestamp": formatted_time,
                "body": body,
                "username": username,
                "sentiment": "neutral" # Default
            }

            if not body:
                empty_count += 1
            else:
                sentiment_info = msg.get("entities", {}).get("sentiment")
                if sentiment_info and isinstance(sentiment_info, dict):
                    sentiment_value = sentiment_info.get("basic")
                    if sentiment_value:
                        sentiment_value = sentiment_value.lower()
                        if sentiment_value == "bullish":
                            bullish_count += 1
                            message_obj["sentiment"] = "bullish"
                        elif sentiment_value == "bearish":
                            bearish_count += 1
                            message_obj["sentiment"] = "bearish"
                        else:
                            neutral_count += 1
                            message_obj["sentiment"] = "neutral"
                    else:
                        neutral_count += 1
                else:
                    neutral_count += 1
            
            messages.append(message_obj) # Добавляем объект сообщения, а не форматированную строку
            if len(messages) >= desired_count:
                break
        if len(messages) >= desired_count or stop:
            break
        
        cursor = json_data.get("cursor", {})
        pagination_max = cursor.get("max")
        if not (cursor.get("more") and pagination_max):
            break
    
    # Теперь fetch_stocktwits_messages возвращает список словарей для messages
    return messages, bullish_count, bearish_count, neutral_count

# --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
def format_stocktwits_data(symbol: str, messages: list, bullish: int, bearish: int, neutral: int) -> str:
    """
    Formats StockTwits data into a standardized JSON string.
    
    Args:
        symbol (str): The stock symbol.
        messages (list): A list of dictionaries, where each dictionary represents a message.
                         Example: [{"timestamp": "...", "body": "...", "username": "...", "sentiment": "..."}]
        bullish (int): Count of bullish messages.
        bearish (int): Count of bearish messages.
        neutral (int): Count of neutral messages.

    Returns:
        str: A JSON formatted string containing the aggregated StockTwits data.
             Returns an empty JSON object "{}" if no messages are available.
    """
    # Создаем словарь Python, который затем будет преобразован в JSON
    stocktwits_dict = {
        "symbol": symbol,
        "sentiment_summary": {
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral
        },
        "messages": messages # Это уже список словарей, как мы модифицировали fetch_stocktwits_messages
    }
    
    # Преобразуем словарь в JSON-строку
    return json.dumps(stocktwits_dict, indent=2, ensure_ascii=False)


def get_stocktwits_context(symbol: str, fetch_limit: int, since_date: datetime) -> str:
    """Get formatted StockTwits data for a symbol."""
    messages, bullish, bearish, neutral = fetch_stocktwits_messages(
        symbol,
        fetch_limit,
        since_date
    )
    # Если сообщений нет, все равно возвращаем валидный JSON с нулевыми значениями
    if not messages and bullish == 0 and bearish == 0 and neutral == 0:
        return json.dumps({
            "symbol": symbol,
            "sentiment_summary": {
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0
            },
            "messages": []
        }, indent=2, ensure_ascii=False)
    
    return format_stocktwits_data(symbol, messages, bullish, bearish, neutral)
