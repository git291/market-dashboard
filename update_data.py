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
        return {'score': 31, 'rating': '恐懼'}


def fetch_chart_data(ticker_symbol, is_daily=False):
    """抓取歷史點位，is_daily=True 抓日線（1個月），否則抓週線抽樣（3個月）"""
    try:
        t = yf.Ticker(ticker_symbol)
        period = '1mo' if is_daily else '3mo'
        hist = t.history(period=period).dropna(subset=['Close'])

        if is_daily:
            sampled = hist  # 日線保留每日點位
        else:
            sampled = hist.iloc[::5]  # 週線抽樣

        chart_data = []
        for idx, row in sampled.iterrows():
            chart_data.append(
                {'time': idx.strftime('%m/%d'), 'price': round(row['Close'], 2)}
            )

        latest_idx = hist.index[-1]
        latest_row = hist.iloc[-1]
        if (
            chart_data
            and chart_data[-1]['time'] != latest_idx.strftime('%m/%d')
        ):
            chart_data.append(
                {
                    'time': latest_idx.strftime('%m/%d'),
                    'price': round(latest_row['Close'], 2),
                }
            )
        return chart_data
    except Exception as e:
        print(f'Error chart {ticker_symbol}: {e}')
        return []


def fetch_market_data():
    tickers = {
        'twii': '^TWII',
        'tsmc': '2330.TW',
        'etf6208': '006208.TW',
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

    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period='1mo').dropna(subset=['Close'])

            if len(hist) >= 2:
                latest_close = hist.iloc[-1]['Close']
                prev_close = hist.iloc[-2]['Close']

                price = round(latest_close, 2)
                prev_price = round(prev_close, 2)
                day_change = round(latest_close - prev_close, 2)
                day_pchange = round((day_change / prev_close) * 100, 2)

                if len(hist) >= 5:
                    w_start_close = hist.iloc[-5]['Close']
                    week_change = round(
                        ((latest_close - w_start_close) / w_start_close) * 100,
                        2,
                    )
                    week_pchange = (
                        f"{'+' if week_change > 0 else ''}{week_change}%"
                    )
                else:
                    week_pchange = '--'

                results[key] = {
                    'price': f'{price:,}',
                    'prev_close': f'{prev_price:,}',
                    'change': abs(day_change),
                    'raw_change': day_change,
                    'pChange': f'{abs(day_pchange)}%',
                    'week_pChange': week_pchange,
                    'open': clean_val(hist.iloc[-1].get('Open')),
                    'high': clean_val(hist.iloc[-1].get('High')),
                    'low': clean_val(hist.iloc[-1].get('Low')),
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
            print(f'Error fetching {key}: {e}')
            results[key] = {
                'price': '--',
                'prev_close': '--',
                'change': '--',
                'pChange': '--',
                'week_pChange': '--',
                'raw_change': 0,
            }

    # 圖表資料 (原油改為日線 is_daily=True)
    results['charts'] = {
        'twii': fetch_chart_data('^TWII', is_daily=False),
        'tsmc': fetch_chart_data('2330.TW', is_daily=False),
        'etf6208': fetch_chart_data('006208.TW', is_daily=False),
        'twd': fetch_chart_data('TWD=X', is_daily=False),
        'brent': fetch_chart_data('BZ=F', is_daily=True),
    }

    results['fear'] = get_fear_and_greed()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    fetch_market_data()
