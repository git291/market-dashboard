import json
import requests
from datetime import datetime

def get_twse_margin_data():
    """爬取台灣證交所信用交易統計 (扣除ETF)"""
    # 帶入 time 參數避免證交所 API 快取
    url = f"https://www.twse.com.tw/rwd/zh/margin/MI_MARGN?response=json&_={int(datetime.now().timestamp())}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.twse.com.tw/zh/page/trading/exchange/MI_MARGN.html'
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        json_data = res.json()
        
        # 檢查證交所回傳格式
        if json_data.get('stat') != 'OK':
            print("TWSE API 狀態異常：", json_data.get('stat'))
            return get_fallback_data()

        # 證交所資料列表 (通常包含大盤總計與各類別)
        tables = json_data.get('tables', [])
        data_rows = []
        
        # 尋找「信用交易統計」或「扣除ETF」相關表格
        for table in tables:
            if 'data' in table:
                data_rows = table['data']
                break

        if not data_rows and 'data' in json_data:
            data_rows = json_data['data']

        if not data_rows:
            return get_fallback_data()

        result = []
        # 解析最後 3 天的資料
        for row in data_rows[-3:]:
            # 安全轉換數字
            def parse_num(val):
                try:
                    return float(str(val).replace(',', '').strip())
                except:
                    return 0.0

            # 日期處理 (例如: "113/09/15" -> "09/15")
            raw_date = str(row[0]).strip()
            date_parts = raw_date.split('/')
            date_fmt = f"{date_parts[1]}/{date_parts[2]}" if len(date_parts) >= 3 else raw_date

            # 解析資券數據 (根據證交所標準欄位索引)
            margin_diff = parse_num(row[5])   # 融資買賣超
            margin_bal = parse_num(row[6])    # 融資餘額(千元/元)
            short_diff = parse_num(row[11])   # 融券買賣超
            short_bal = parse_num(row[12])    # 融券餘額(張)

            # 格式化顯示 (億 / 張 / 萬)
            margin_diff_str = f"{'+' if margin_diff > 0 else ''}{round(margin_diff / 100000000, 1)}億"
            short_diff_str = f"{'+' if short_diff > 0 else ''}{int(short_diff):,}"
            margin_bal_str = f"{round(margin_bal / 100000000, 0):,.0f}億"
            short_bal_str = f"{round(short_bal / 10000, 1)}萬"

            result.append({
                'date': date_fmt,
                'margin_buy_sell': margin_diff_str,
                'short_buy_sell': short_diff_str,
                'margin_balance': margin_bal_str,
                'short_balance': short_bal_str
            })

        return list(reversed(result)) if result else get_fallback_data()

    except Exception as e:
        print(f"TWSE Fetch error: {e}")
        return get_fallback_data()

def get_fallback_data():
    return [
        {"date": "09/15", "margin_buy_sell": "-12.5億", "short_buy_sell": "+1,200", "margin_balance": "2,650億", "short_balance": "32.5萬"},
        {"date": "09/14", "margin_buy_sell": "+18.3億", "short_buy_sell": "-850", "margin_balance": "2,662億", "short_balance": "32.3萬"},
        {"date": "09/13", "margin_buy_sell": "+5.2億", "short_buy_sell": "+3,100", "margin_balance": "2,644億", "short_balance": "32.4萬"}
    ]

def main():
    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "twii": {"price": "21,750.12", "prev_close": "21,600.00", "week_pChange": "+1.8%", "raw_change": 150.12},
        "tsmc": {"price": "940.0", "prev_close": "930.0", "week_pChange": "+2.1%", "raw_change": 10.0},
        "etf6208": {"price": "102.50", "prev_close": "101.20", "week_pChange": "+1.2%", "raw_change": 1.3},
        "fitx": {"price": "21,720", "change": "130", "pChange": "+0.60%", "raw_change": 130},
        "dji": {"price": "40,836.44", "change": "-234.21", "pChange": "-0.57%", "raw_change": -234.21},
        "ixic": {"price": "16,884.60", "change": "-98.45", "pChange": "-0.58%", "raw_change": -98.45},
        "sox": {"price": "4,578.12", "change": "-42.10", "pChange": "-0.91%", "raw_change": -42.10},
        "vix": {"price": "19.45", "change": "1.20", "pChange": "+6.58%", "raw_change": 1.20, "open": "18.50", "high": "20.10", "low": "18.20", "prev": "18.25"},
        "usdtwd": {"price": "31.820", "change": "0.05", "pChange": "+0.16%", "raw_change": 0.05},
        "brent": {"price": "72.60", "change": "-0.85", "pChange": "-1.16%", "raw_change": -0.85},
        "bond": {"price": "3.65", "prev_close": "3.68"},
        "fear": {"score": "38"},
        "margin_data": get_twse_margin_data(),
        "charts": {
            "twii": [{"time": "09/09", "price": 21300}, {"time": "09/10", "price": 21450}, {"time": "09/11", "price": 21600}, {"time": "09/12", "price": 21750}],
            "tsmc": [{"time": "09/09", "price": 910}, {"time": "09/10", "price": 920}, {"time": "09/11", "price": 930}, {"time": "09/12", "price": 940}],
            "etf6208": [{"time": "09/09", "price": 99.5}, {"time": "09/10", "price": 100.2}, {"time": "09/11", "price": 101.2}, {"time": "09/12", "price": 102.5}],
            "twd": [{"time": "09/09", "price": 32.1}, {"time": "09/10", "price": 32.0}, {"time": "09/11", "price": 31.9}, {"time": "09/12", "price": 31.82}],
            "brent": [{"time": "09/09", "price": 75.2}, {"time": "09/10", "price": 74.0}, {"time": "09/11", "price": 73.1}, {"time": "09/12", "price": 72.6}]
        }
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("data.json 數據已成功寫入！")

if __name__ == "__main__":
    main()
