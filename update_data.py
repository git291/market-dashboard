from datetime import datetime
import json
import requests
import yfinance as yf


def clean_val(val, default='--'):
    try:
        if val is None or str(val).lower() == 'nan':
            return default
        return round(float(val), 2)
    except:
        return default


def get_fear_and_greed():
    url = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        print(f'Fear & Greed fetch error: {e}')
        return {'score': 33, 'rating': '恐懼'}


def fetch_market_data():
    tickers = {
        'dji': '^DJI',  # 道瓊
        'ixic': '^IXIC',  # 那斯達克
        'sox': '^SOX',  # 費城半導體
        'fitx': '^TWII',  # 台股大盤 / 台指期代表
        'usdtwd': 'TWD=X',  # 美元/台幣
        'vix': '^VIX',  # VIX
        'brent': 'BZ=F',  # 布蘭特原油
        'bond': '^TNX',  # 美國 10 年期公債殖利率
    }

    results = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S (CST)')
    }

    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period='5d')

            # 排除 NaN 列
            hist = hist.dropna(subset=['Close'])

            if len(hist) >= 2:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]

                price_raw = latest['Close']
                prev_raw = prev['Close']

                price = round(price_raw, 2)
                change = round(price_raw - prev_raw, 2)
                p_change = round((change / prev_raw) * 100, 2)

                results[key] = {
                    'price': f'{price:,}',
                    'change': change,
                    'raw_change': change,
                    'pChange': f'{p_change}%',
                    'open': clean_val(latest.get('Open')),
                    'high': clean_val(latest.get('High')),
                    'low': clean_val(latest.get('Low')),
                    'prev': clean_val(prev_raw),
                }
            else:
                results[key] = {
                    'price': '--',
                    'change': '--',
                    'pChange': '--',
                    'raw_change': 0,
                }
        except Exception as e:
            print(f'Error fetching {key}: {e}')
            results[key] = {
                'price': '--',
                'change': '--',
                'pChange': '--',
                'raw_change': 0,
            }

    results['fear'] = get_fear_and_greed()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    fetch_market_data()
