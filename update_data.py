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


def get_twse_margin_data():
    """爬取台灣證交所信用交易統計 (扣除ETF)"""
    url = 'https://www.twse.com.tw/rwd/zh/margin/MI_MARGN?response=json'
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        json_data = res.json()

        if json_data.get('stat') != 'OK':
            return []

        # 取得數據列表
        raw_rows = json_data.get('data', [])
        result = []

        # 抓取最新前 6 筆交易日資料
        for row in raw_rows[:6]:
            date_str = row[0]  # 例: "113/09/14"
            date_fmt = (
                f"{date_str.split('/')[1]}/{date_str.split('/')[2]}"
                if '/' in date_str
                else date_str
            )

            # 融資買賣超與餘額 (單位: 仟元/張)
            # 依證交所欄位格式解析
            result.append({
                'date': date_fmt,
                'margin_buy_sell': row[5],  # 融資買賣超
                'short_buy_sell': row[11],  # 融券買賣超
                'margin_balance': (
                    f'{round(float(row[6].replace(",", "")) / 100000000, 2)}億'
                ),  # 融資餘額 (億)
                'short_balance': (
                    f'{round(float(row[12].replace(",", "")) / 10000, 2)}萬'
                ),  # 融券餘額 (萬張)
            })
        return result
    except Exception as e:
        print(f'TWSE Margin fetch error: {e}')
        return []


def fetch_chart_data(ticker_symbol, is_daily=False):
    try:
        t = yf.Ticker(ticker_symbol)
        period = '1mo' if is_daily else '3mo'
        hist = t.history(period=period).dropna(subset=['Close'])

        sampled = hist if is_daily else hist.iloc[::5]
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
        'bond': '^TNX',  # 美國10年期公債殖利率
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
                    'open': '--',
                    'high': '--',
                    'low': '--',
                    'prev': '--',
                }
        except Exception as e:
            print(f'Error fetching {key}: {e}')

    # 抓取信用交易統計
    results['margin_data'] = get_twse_margin_data()

    # 圖表資料
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
