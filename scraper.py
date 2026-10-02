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
    # 直接請求玩股網微台指散戶多空比的 API 端點
    url = "https://www.wantgoo.com/investor/retail-indicator/wtm-data"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.wantgoo.com/futures/retail-indicator/wtm",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"API 請求失敗，HTTP 狀態碼: {response.status_code}")
            return None

        data = response.json()
        if not data or not isinstance(data, list):
            print("API 未回傳有效的 JSON 陣列")
            return None

        # 取得最新的第一筆資料
        latest = data[0]
        
        # 處理日期格式 (例如 API 回傳 "2026-10-02" 轉成 "2026/10/02")
        raw_date = str(latest.get("date", "")).replace("-", "/")
        
        return {
            "date": raw_date,
            "price": str(latest.get("price", "")),
            "long": str(latest.get("long", "")),
            "short": str(latest.get("short", "")),
            "ratio": str(latest.get("ratio", ""))
        }
    except Exception as e:
        print(f"請求 API 發生例外錯誤: {e}")
        
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
                f"收盤價：{data['price']}\n"
                f"散戶多空比：{data['ratio']}%\n"
                f"做多：{data['long']} | 做空：{data['short']}"
            )
            send_telegram_msg(msg)
            print("已成功發送通知！")
        else:
            print(f"今日 ({today_str}) 資料尚未更新，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
