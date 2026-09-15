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


def fetch_market_data():
    tickers = {
        'twii': '^TWII',  # 台股大盤
        'tsmc': '2330.TW',  # 台積電
        'etf6208': '006208.TW',  # 富邦台50
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
            # 抓取近 1 個月的日資料 (最穩定，避免週線 API 失敗)
            hist = t.history(period='1mo').dropna(subset=['Close'])

            if len(hist) >= 2:
                latest_close = hist.iloc[-1]['Close']
                prev_close = hist.iloc[-2]['Close']

                # 最新價格與當日變動
                price = round(latest_close, 2)
                prev_price = round(prev_close, 2)
                day_change = round(latest_close - prev_close, 2)
                day_pchange = round((day_change / prev_close) * 100, 2)

                # 計算近 5 個交易日(週線)變動幅度
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
            print(f'Error fetching {key} ({symbol}): {e}')
            results[key] = {
                'price': '--',
                'prev_close': '--',
                'change': '--',
                'pChange': '--',
                'week_pChange': '--',
                'raw_change': 0,
            }

    # 抓取台幣近 12 週的歷史週線資料
    try:
        twd = yf.Ticker('TWD=X')
        # 取 3 個月的日資料，每 5 個交易日抽樣一次模擬週線點位
        twd_hist = twd.history(period='3mo').dropna(subset=['Close'])
        chart_data = []

        # 隔 5 天取一筆日 K 形成週趨勢點
        sampled_hist = twd_hist.iloc[::5]
        for idx, row in sampled_hist.iterrows():
            chart_data.append(
                {'time': idx.strftime('%m/%d'), 'price': round(row['Close'], 3)}
            )

        # 確保包含最新的一筆點位
        latest_idx = twd_hist.index[-1]
        latest_row = twd_hist.iloc[-1]
        if chart_data[-1]['time'] != latest_idx.strftime('%m/%d'):
            chart_data.append(
                {
                    'time': latest_idx.strftime('%m/%d'),
                    'price': round(latest_row['Close'], 3),
                }
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
