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
    url = "https://blave.org/api/studio/twstock/market/futures-retail-long-short-ratio?symbol=wtm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://blave.org/studio/twstock/zh/market/futures_retail_long_short_ratio"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"請求失敗，HTTP 狀態碼: {response.status_code}")
            return None

        json_data = response.json()
        items = json_data.get("data", []) if isinstance(json_data, dict) else json_data
        
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
        else:
            print(f"API 回傳資料結構為空: {json_data}")
    except Exception as e:
        print(f"解析發生錯誤: {e}")
        
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
