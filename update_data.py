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
    # 基礎市場清單
    tickers = {
        'dji': '^DJI',
        'ixic': '^IXIC',
        'sox': '^SOX',
        'fitx': '^TWII',
        'usdtwd': 'TWD=X',
        'vix': '^VIX',
        'brent': 'BZ=F',
        'bond': '^TNX',
        # 新增頂部三大指標
        'twii': '^TWII',  # 台股大盤
        'tsmc': '2330.TW',  # 台積電
        'etf6208': '006208.TW',  # 富邦台50 (006208)
    }

    results = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S (CST)')
    }

    # 抓取常規與頂部數據 (含日收盤與週變化)
    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            # 抓取日資料算前一日收盤價
            hist_d = t.history(period='5d').dropna(subset=['Close'])
            # 抓取週資料算週線趨勢
            hist_w = t.history(period='1mo', interval='1wk').dropna(
                subset=['Close']
            )

            if len(hist_d) >= 2:
                latest = hist_d.iloc[-1]
                prev = hist_d.iloc[-2]
                price = round(latest['Close'], 2)
                prev_close = round(prev['Close'], 2)
                day_change = round(price - prev_close, 2)
                day_pchange = round((day_change / prev_close) * 100, 2)

                # 週線計算 (最新週 vs 前一週)
                week_pchange = '--'
                if len(hist_w) >= 2:
                    w_latest = hist_w.iloc[-1]['Close']
                    w_prev = hist_w.iloc[-2]['Close']
                    w_change = w_latest - w_prev
                    week_pchange = f'{round((w_change / w_prev) * 100, 2)}%'

                results[key] = {
                    'price': f'{price:,}',
                    'prev_close': f'{prev_close:,}',
                    'change': abs(day_change),
                    'raw_change': day_change,
                    'pChange': f'{abs(day_pchange)}%',
                    'week_pChange': week_pchange,
                    'open': clean_val(latest.get('Open')),
                    'high': clean_val(latest.get('High')),
                    'low': clean_val(latest.get('Low')),
                    'prev': clean_val(prev_close),
                }
            else:
                results[key] = {
                    'price': '--',
                    'prev_close': '--',
                    'change': '--',
                    'pChange': '--',
                    'week_pChange': '--',
                    'raw_change': 0,
                }
        except Exception as e:
            print(f'Error {key}: {e}')
            results[key] = {
                'price': '--',
                'prev_close': '--',
                'change': '--',
                'pChange': '--',
                'week_pChange': '--',
                'raw_change': 0,
            }

    # 抓取台幣走勢圖：改為「週線趨勢」數據 (半年每週資料, 1wk)
    try:
        twd_ticker = yf.Ticker('TWD=X')
        twd_weekly = twd_ticker.history(period='6mo', interval='1wk').dropna(
            subset=['Close']
        )
        chart_data = []
        for idx, row in twd_weekly.iterrows():
            chart_data.append(
                {'time': idx.strftime('%m/%d'), 'price': round(row['Close'], 3)}
            )
        results['twd_chart'] = chart_data
    except Exception as e:
        print(f'TWD Weekly Chart error: {e}')
        results['twd_chart'] = []

    results['fear'] = get_fear_and_greed()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    fetch_market_data()
