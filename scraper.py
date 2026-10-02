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
    # 台灣期貨交易所 (TAIFEX) 官方 Open API - 微型台指散戶多空比
    url = "https://openapi.taifex.com.tw/v1/DailyRetailLongShortRatio"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"請求期交所 API 失敗，HTTP 狀態碼: {response.status_code}")
            return None

        data_list = response.json()
        
        # 期交所 API 回傳陣列，最後一筆通常是最新日期的資料
        if data_list and isinstance(data_list, list):
            latest = data_list[-1]
            
            # API 回傳西元年格式 (如 "20261002") 或民國年，轉為 "2026/10/02"
            raw_date_str = str(latest.get("Date", ""))
            if len(raw_date_str) == 8:
                date_formatted = f"{raw_date_str[:4]}/{raw_date_str[4:6]}/{raw_date_str[6:]}"
            else:
                date_formatted = raw_date_str
            
            # 讀取期交所欄位 (包含散戶多空口數與比例)
            long_cnt = latest.get("RetailLongContracts", latest.get("LongContracts", 0))
            short_cnt = latest.get("RetailShortContracts", latest.get("ShortContracts", 0))
            ratio_val = latest.get("RetailLongShortRatio", 0)
            price_val = latest.get("ClosePrice", latest.get("TAIEX", "0"))
            
            return {
                "date": date_formatted,
                "price": f"{price_val}",
                "long": f"{int(long_cnt):,}" if str(long_cnt).isdigit() else str(long_cnt),
                "short": f"{int(short_cnt):,}" if str(short_cnt).isdigit() else str(short_cnt),
                "ratio": f"{float(ratio_val):+.2f}%" if isinstance(ratio_val, (int, float)) else f"{ratio_val}%"
            }
        else:
            print(f"期交所 API 回傳格式為空")
    except Exception as e:
        print(f"呼叫期交所 API 失敗: {e}")
        
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
                f"收盤/指數：{data['price']}\n"
                f"散戶多空比：{data['ratio']}\n"
                f"做多：{data['long']} 口 | 做空：{data['short']} 口"
            )
            send_telegram_msg(msg)
            print("已成功發送通知！")
        else:
            print(f"今日 ({today_str}) 資料尚未更新或日期不不符，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
