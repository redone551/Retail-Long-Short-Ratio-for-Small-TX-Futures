import os
import requests
from datetime import datetime, timezone, timedelta

# 設定台灣時區 (UTC+8)
TZ_TW = timezone(timedelta(hours=8))

# Telegram 設定
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("未設定 Telegram Token 或 Chat ID")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, data=payload, timeout=10)
        print(f"Telegram API 回應: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"發送通知失敗: {e}")

def fetch_data():
    # 台灣期貨交易所 (Taifex) 官方每日交易資訊 Open Data API
    url = "https://openapi.taifex.com.tw/v1/DailyMarketReport"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # 先從期交所每日統計或散戶多空比 API 端點獲取資料
        # 若需要精準散戶多空比，直接抓取 Blave 前端靜態頁面數據 (帶完整的標準網頁 Request)
        blave_url = "https://blave.org/studio/twstock/zh/market/futures_retail_long_short_ratio"
        
        # 使用 requests 抓取 Blave 頁面並透過解析內嵌的 Next.js / React State 數據
        res = requests.get(blave_url, headers=headers, timeout=15)
        if res.status_code == 200 and "__NEXT_DATA__" in res.text:
            import json
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script:
                json_obj = json.loads(next_data_script.string)
                # 從 SSR React hydration state 讀取第一筆數據
                props = json_obj.get("props", {}).get("pageProps", {})
                items = props.get("data", []) or props.get("initialData", [])
                
                if items and isinstance(items, list):
                    latest = items[0]
                    raw_date = str(latest.get("date", "")).replace("-", "/")
                    
                    price = f"{latest.get('close', 0):,}" if latest.get('close') else str(latest.get('price', ''))
                    long_cnt = f"{latest.get('long', 0):,}" if latest.get('long') else str(latest.get('long', ''))
                    short_cnt = f"{latest.get('short', 0):,}" if latest.get('short') else str(latest.get('short', ''))
                    ratio = f"{latest.get('ratio', 0):+.2f}%" if latest.get('ratio') is not None else str(latest.get('ratio', ''))
                    
                    return {
                        "date": raw_date,
                        "price": price,
                        "long": long_cnt,
                        "short": short_cnt,
                        "ratio": ratio
                    }
        
        # 備用方案：解析 Blave HTML 上的表格列數據
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, "html.parser")
        first_row = soup.find("table").find("tbody").find("tr") if soup.find("table") else None
        if first_row:
            cols = [td.text.strip() for td in first_row.find_all(["td", "th"])]
            if len(cols) >= 6:
                return {
                    "date": cols[0].replace("-", "/"),
                    "price": cols[1],
                    "long": cols[2],
                    "short": cols[3],
                    "ratio": cols[5]
                }
    except Exception as e:
        print(f"解析發生例外錯誤: {e}")
        
    return None

def main():
    today_str = datetime.now(TZ_TW).strftime("%Y/%m/%d")
    print(f"檢查日期: {today_str}")

    try:
        data = fetch_data()
        print(f"爬取結果: {data}")

        if data and data['date'] == today_str:
            msg = (
                f"【微台指散戶多空比已更新】\n"
                f"日期：{data['date']}\n"
                f"加權指數：{data['price']}\n"
                f"散戶多空比：{data['ratio']}\n"
                f"做多：{data['long']} 口 | 做空：{data['short']} 口"
            )
            send_telegram_msg(msg)
            print("已成功發送通知！")
        else:
            print(f"今日 ({today_str}) 資料尚未更新，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
