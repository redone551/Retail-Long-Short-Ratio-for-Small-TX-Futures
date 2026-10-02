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
    # 期交所 DailyRetailLongShortRatio API 端點
    url = "https://openapi.taifex.com.tw/v1/DailyRetailLongShortRatio"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"期交所 API 回傳 HTTP {response.status_code}")
            return None

        # 安全解析 JSON
        try:
            data_list = response.json()
        except Exception as json_err:
            print(f"解析期交所 JSON 失敗: {json_err}, 回應前 100 字元: {response.text[:100]}")
            return None

        if data_list and isinstance(data_list, list):
            latest = data_list[-1]
            
            # 期交所 API 欄位解析
            raw_date_str = str(latest.get("Date", ""))
            if len(raw_date_str) == 8:
                date_formatted = f"{raw_date_str[:4]}/{raw_date_str[4:6]}/{raw_date_str[6:]}"
            else:
                date_formatted = raw_date_str
            
            # 取得各項欄位數據
            long_cnt = latest.get("RetailLongContracts") or latest.get("LongContracts") or 0
            short_cnt = latest.get("RetailShortContracts") or latest.get("ShortContracts") or 0
            ratio_val = latest.get("RetailLongShortRatio") or 0
            price_val = latest.get("ClosePrice") or latest.get("TAIEX") or "0"
            
            return {
                "date": date_formatted,
                "price": str(price_val),
                "long": f"{int(long_cnt):,}" if str(long_cnt).isdigit() or isinstance(long_cnt, (int, float)) else str(long_cnt),
                "short": f"{int(short_cnt):,}" if str(short_cnt).isdigit() or isinstance(short_cnt, (int, float)) else str(short_cnt),
                "ratio": f"{float(ratio_val):+.2f}%" if isinstance(ratio_val, (int, float)) else f"{ratio_val}%"
            }
        else:
            print("期交所 API 回傳空列表")
    except Exception as e:
        print(f"請求發生例外錯誤: {e}")
        
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
            print(f"今日 ({today_str}) 資料尚未更新或日期不符，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
