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
        print(f'Fear & Greed error: {e}')
        return {'score': 33, 'rating': '恐懼'}


def fetch_market_data():
    tickers = {
        'dji': '^DJI',
        'ixic': '^IXIC',
        'sox': '^SOX',
        'fitx': '^TWII',
        'usdtwd': 'TWD=X',
        'vix': '^VIX',
        'brent': 'BZ=F',
        'bond': '^TNX',
    }

    results = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S (CST)')
    }

    # 抓取各項行情
    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period='5d').dropna(subset=['Close'])

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
                    'change': abs(change),
                    'raw_change': change,
                    'pChange': f'{abs(p_change)}%',
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
            print(f'Error {key}: {e}')
            results[key] = {
                'price': '--',
                'change': '--',
                'pChange': '--',
                'raw_change': 0,
            }

    # 抓取台幣今日真實 5 分鐘走勢圖數據
    try:
        twd_ticker = yf.Ticker('TWD=X')
        twd_hist = twd_ticker.history(period='1d', interval='5m')
        chart_data = []
        for idx, row in twd_hist.iterrows():
            chart_data.append(
                {'time': idx.strftime('%H:%M'), 'price': round(row['Close'], 3)}
            )
        results['twd_chart'] = chart_data
    except Exception as e:
        print(f'TWD Chart error: {e}')
        results['twd_chart'] = []

    results['fear'] = get_fear_and_greed()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    fetch_market_data()
