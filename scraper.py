import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 設定台灣時區 (UTC+8)
TZ_TW = timezone(timedelta(hours=8))

# Telegram 設定
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8690257630:AAHbWsmER4ZGxiaVCGd151bk8ljbg_uxztI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "984292295")

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
    # 修正網址：移除末尾多餘的 &
    url = "https://www.wantgoo.com/futures/retail-indicator/wtm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        print(f"網頁請求失敗，HTTP 狀態碼: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    if not table:
        print("找不到資料表格")
        return None
        
    first_row = table.find('tbody').find('tr') if table.find('tbody') else table.find_all('tr')[1]
    cols = [td.text.strip() for td in first_row.find_all(['td', 'th'])]
    
    if len(cols) >= 5:
        return {
            "date": cols[0],
            "price": cols[1],
            "long": cols[2],
            "short": cols[3],
            "ratio": cols[4]
        }
    return None

def main():
    # 1. 程式一啟動立刻發送測試訊息，確認 Telegram 連線正常
    send_telegram_msg("測試：GitHub Actions 爬蟲程式已成功啟動！")
    
    today_str = datetime.now(TZ_TW).strftime("%Y/%m/%d")
    max_retries = 24  # 最多嘗試 2 小時 (24 次)
    interval_seconds = 300  # 間隔 5 分鐘
    
    print(f"開始執行輪詢，目標日期: {today_str}")
    
    for i in range(max_retries):
        try:
            data = fetch_data()
            print(f"爬取結果: {data}")
            
            # 如果抓到的最新日期等於今天
            if data and data['date'] == today_str:
                msg = (
                    f"【微台指散戶多空比已更新】\n"
                    f"日期：{data['date']}\n"
                    f"收盤價：{data['price']}\n"
                    f"散戶多空比：{data['ratio']}%\n"
                    f"做多：{data['long']} | 做空：{data['short']}"
                )
                send_telegram_msg(msg)
                return  # 抓到資料後結束程式
            else:
                print(f"[{datetime.now(TZ_TW).strftime('%H:%M:%S')}] 資料尚未更新至 {today_str}，5分鐘後重試...")
        except Exception as e:
            print(f"抓取過程發生例外狀況: {e}")
            
        time.sleep(interval_seconds)
        
    send_telegram_msg(f"警告：截至 {datetime.now(TZ_TW).strftime('%H:%M')} 仍未爬取到 {today_str} 的微台指散戶多空比資料。")

if __name__ == "__main__":
    main()
