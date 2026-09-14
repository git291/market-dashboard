from datetime import datetime
import json
import requests
import yfinance as yf


# 1. 抓取 CNN 恐懼與貪婪指數
def get_fear_and_greed():
    url = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        score = round(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']

        rating_map = {
            'extreme fear': '極度恐懼',
            'fear': '恐懼',
            'neutral': '中立',
            'greed': '貪婪',
            'extreme greed': '極度貪婪',
        }
        return {
            'score': score,
            'rating': rating_map.get(rating.lower(), rating),
        }
    except Exception as e:
        print(f'Fear & Greed fetch failed: {e}')
        return {'score': '--', 'rating': '無法讀取'}


# 2. 主抓取流程
def fetch_market_data():
    tickers = {
        'dji': '^DJI',  # 道瓊指數
        'ixic': '^IXIC',  # 那斯達克
        'sox': '^SOX',  # 費城半導體
        'fitx': 'WTX=F',  # 台指期近月
        'usdtwd': 'TWD=X',  # 美元/台幣
        'vix': '^VIX',  # VIX
        'brent': 'BZ=F',  # 布蘭特原油
    }

    results = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S (CST)')
    }

    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period='5d')  # 取 5 天確保避開休市日
            if len(hist) >= 2:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]

                price = round(latest['Close'], 2)
                change = round(price - prev['Close'], 2)
                p_change = round((change / prev['Close']) * 100, 2)

                results[key] = {
                    'price': f'{price:,}',
                    'change': change,
                    'pChange': f'{p_change}%',
                    'open': round(latest['Open'], 2),
                    'high': round(latest['High'], 2),
                    'low': round(latest['Low'], 2),
                    'prev': round(prev['Close'], 2),
                }
            else:
                results[key] = {'price': '--', 'change': '--', 'pChange': '--'}
        except Exception as e:
            print(f'Error fetching {key}: {e}')
            results[key] = {'price': '--', 'change': '--', 'pChange': '--'}

    # 寫入恐懼與貪婪指數
    results['fear'] = get_fear_and_greed()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    fetch_market_data()
