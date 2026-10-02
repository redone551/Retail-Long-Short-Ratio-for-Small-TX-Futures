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
        print(f"Telegram API 回應: {res.status_code}")
    except Exception as e:
        print(f"發送通知失敗: {e}")

def fetch_data():
    # 玩股网 (WantGoo) 微台散戶多空比 API，不阻擋 GitHub Actions IP
    url = "https://www.wantgoo.com/investor/retail/small-tx-futures-ratio-data"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.wantgoo.com/investor/retail/small-tx-futures-ratio"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data_list = res.json()
            if data_list and isinstance(data_list, list):
                # 取得最新的一筆數據
                latest = data_list[0]
                
                # 格式化日期 (原始格式如 "2026/10/02" 或 "2026-10-02")
                raw_date = str(latest.get("date", "")).replace("-", "/")
                
                price = latest.get("close") or latest.get("price") or 0
                long_cnt = latest.get("long") or 0
                short_cnt = latest.get("short") or 0
                ratio_val = latest.get("ratio") or 0
                
                return {
                    "date": raw_date,
                    "price": f"{int(price):,}" if isinstance(price, (int, float)) else str(price),
                    "long": f"{int(long_cnt):,}" if isinstance(long_cnt, (int, float)) else str(long_cnt),
                    "short": f"{int(short_cnt):,}" if isinstance(short_cnt, (int, float)) else str(short_cnt),
                    "ratio": f"{float(ratio_val):+.2f}%" if isinstance(ratio_val, (int, float)) else f"{ratio_val}%"
                }
    except Exception as e:
        print(f"抓取玩股網 API 失敗: {e}")
        
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
                f"加權指數/收盤：{data['price']}\n"
                f"散戶多空比：{data['ratio']}\n"
                f"做多：{data['long']} 口 | 做空：{data['short']} 口"
            )
            send_telegram_msg(msg)
            print("已成功發送通知！")
        else:
            print(f"今日 ({today_str}) 資料尚未更新或日期不符，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
