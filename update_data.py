import json
import requests
from datetime import datetime
import yfinance as yf

def fetch_real_data():
    """使用 yfinance 動態抓取全球最新市場真實數據"""
    symbols = {
        'twii': '^TWII',        # 台股加權指數
        'tsmc': '2330.TW',      # 台積電
        'etf6208': '006208.TW',  # 富邦台50
        'fitx': '^TWII',        # 台指期 (以加權指數走勢替代)
        'dji': '^DJI',          # 道瓊
        'ixic': '^IXIC',        # 那斯達克
        'sox': '^SOX',          # 費半
        'vix': '^VIX',          # VIX
        'usdtwd': 'TWD=X',      # 美元台幣
        'brent': 'BZ=F',        # 布蘭特原油
        'bond': '^TNX'          # 美國10年期公債
    }

    market_data = {}
    charts_data = {}

    for key, sym in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="7d")

            if not hist.empty and len(hist) >= 2:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]

                price = float(latest['Close'])
                prev_close = float(prev['Close'])
                change = price - prev_close
                p_change = (change / prev_close) * 100

                # 價格格式化
                if price >= 1000:
                    price_str = f"{price:,.2f}"
                    prev_str = f"{prev_close:,.2f}"
                else:
                    price_str = f"{price:.2f}"
                    prev_str = f"{prev_close:.2f}"

                market_data[key] = {
                    "price": price_str,
                    "change": f"{change:+.2f}",
                    "pChange": f"{p_change:+.2f}%",
                    "week_pChange": f"{p_change:+.2f}%",
                    "prev_close": prev_str,
                    "raw_change": change
                }

                # 自動提取真實近 5 日圖表走勢
                chart_points = []
                for idx, row in hist.tail(5).iterrows():
                    chart_points.append({
                        "time": idx.strftime("%m/%d"),
                        "price": round(float(row['Close']), 2)
                    })
                charts_data[key] = chart_points
            else:
                market_data[key] = {"price": "--", "change": "--", "pChange": "--", "raw_change": 0}
        except Exception as e:
            print(f"Fetch error on {key} ({sym}): {e}")
            market_data[key] = {"price": "--", "change": "--", "pChange": "--", "raw_change": 0}

    # 補充 VIX 開高低收
    try:
        vix_hist = yf.Ticker('^VIX').history(period="2d").iloc[-1]
        if 'vix' in market_data:
            market_data['vix'].update({
                "open": f"{vix_hist['Open']:.2f}",
                "high": f"{vix_hist['High']:.2f}",
                "low": f"{vix_hist['Low']:.2f}",
                "prev": market_data['vix']['prev_close']
            })
    except Exception as e:
        print(f"VIX details error: {e}")

    return market_data, charts_data

def fetch_twse_margin():
    """抓取證交所真實資券資料"""
    url = f"https://www.twse.com.tw/rwd/zh/margin/MI_MARGN?response=json&_={int(datetime.now().timestamp())}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        json_data = res.json()
        if json_data.get('stat') == 'OK':
            raw_rows = json_data.get('data', [])
            if not raw_rows and 'tables' in json_data:
                for t in json_data['tables']:
                    if t.get('data'):
                        raw_rows = t['data']
                        break
            
            result = []
            for row in raw_rows[-3:]:
                def parse_num(v):
                    try: return float(str(v).replace(',', '').strip())
                    except: return 0.0

                date_str = str(row[0]).strip()
                d_parts = date_str.split('/')
                date_fmt = f"{int(d_parts[1]):02d}/{int(d_parts[2]):02d}" if len(d_parts) == 3 else date_str

                m_diff, m_bal = parse_num(row[5]), parse_num(row[6])
                s_diff, s_bal = parse_num(row[11]), parse_num(row[12])

                result.append({
                    'date': date_fmt,
                    'margin_buy_sell': f"{'+' if m_diff > 0 else ''}{round(m_diff / 100000000, 1)}億",
                    'short_buy_sell': f"{'+' if s_diff > 0 else ''}{int(s_diff):,}",
                    'margin_balance': f"{round(m_bal / 100000000, 0):,.0f}億" if m_bal > 1000000 else f"{round(m_bal / 10000, 1)}萬",
                    'short_balance': f"{round(s_bal / 10000, 1)}萬"
                })
            return list(reversed(result))
    except Exception as e:
        print(f"Margin error: {e}")
    return []

def main():
    print("開始抓取全球即時市場數據...")
    m_data, c_data = fetch_real_data()
    margin_data = fetch_twse_margin()

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "twii": m_data.get("twii", {}),
        "tsmc": m_data.get("tsmc", {}),
        "etf6208": m_data.get("etf6208", {}),
        "fitx": m_data.get("fitx", {}),
        "dji": m_data.get("dji", {}),
        "ixic": m_data.get("ixic", {}),
        "sox": m_data.get("sox", {}),
        "vix": m_data.get("vix", {}),
        "usdtwd": m_data.get("usdtwd", {}),
        "brent": m_data.get("brent", {}),
        "bond": m_data.get("bond", {}),
        "fear": {"score": "38"},
        "margin_data": margin_data,
        "charts": c_data
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("實時資料已寫入 data.json！")

if __name__ == "__main__":
    main()
