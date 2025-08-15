
#### Пример кода:

import requests
from bs4 import BeautifulSoup
import json
import time

# Функция для получения новостей по одному тикеру
def get_news_for_ticker(ticker, max_news=30):
    url = f'https://seekingalpha.com/symbol/{ticker}/news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/107.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve data for {ticker}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('div', class_='article')
    news_list = []

    for article in articles:
        if len(news_list) >= max_news:
            break
        title_tag = article.find('h2', class_='article-title')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.find('a')['href']
        date_tag = article.find('time')
        date = date_tag['datetime'] if date_tag else ''
        summary_tag = article.find('div', class_='article-summary')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        news_list.append({
            'title': title,
            'link': link,
            'date': date,
            'summary': summary
        })
    return news_list

# Список крупнейших 6 тикеров
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'FB']

result = {}

for ticker in tickers:
    print(f"Collecting news for {ticker}...")
    news = get_news_for_ticker(ticker, max_news=30)
    result[ticker] = news
    time.sleep(5)  # уважительный интервал между запросами

# Вывод результата в JSON формате
json_output = json.dumps(result, ensure_ascii=False, indent=2)
print(json_output)
#---------------------------------------------------------------------------
# (crew) PS C:\Users\user\AITradingCrew> python seekingalpha.py
# Collecting news for AAPL...
# Failed to retrieve data for AAPL
# Collecting news for MSFT...
# Failed to retrieve data for MSFT
# Collecting news for GOOGL...
# Failed to retrieve data for GOOGL
# Collecting news for AMZN...
# Failed to retrieve data for AMZN
# Collecting news for TSLA...
# Failed to retrieve data for TSLA
# Collecting news for FB...
# Failed to retrieve data for FB
# {
  # "AAPL": [],
  # "MSFT": [],
  # "GOOGL": [],
  # "AMZN": [],
  # "TSLA": [],
  # "FB": []
# }