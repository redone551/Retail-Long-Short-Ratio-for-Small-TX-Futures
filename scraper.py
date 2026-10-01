import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 設定台灣時區 (UTC+8)
TZ_TW = timezone(timedelta(hours=8))

# 1. Telegram 通知設定 (需替換為你的 Token 與 Chat ID)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8690257630:AAHbWsmER4ZGxiaVCGd151bk8ljbg_uxztI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "984292295")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"發送通知失敗: {e}")

def fetch_data():
    url = "https://www.wantgoo.com/futures/retail-indicator/wtm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 解析表格第一行資料（最新一天）
    table = soup.find('table')
    if not table:
        return None
        
    first_row = table.find('tbody').find('tr') if table.find('tbody') else table.find_all('tr')[1]
    cols = [td.text.strip() for td in first_row.find_all(['td', 'th'])]
    
    # 欄位順序：[日期, 收盤價, 散戶做多, 散戶做空, 散戶多空比(%)]
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
    today_str = datetime.now(TZ_TW).strftime("%Y/%m/%d")
    
    max_retries = 36  # 每 5 分鐘一次，最多嘗試 2 Hours (24次)
    interval_seconds = 300 # 5 分鐘
    
    print(f"開始執行輪詢，目標日期: {today_str}")
    
    for i in range(max_retries):
        try:
            data = fetch_data()
            if data and data['date'] == today_str:
                msg = (
                    f"【微台指散戶多空比已更新】\n"
                    f"日期：{data['date']}\n"
                    f"收盤價：{data['price']}\n"
                    f"散戶多空比：{data['ratio']}%\n"
                    f"做多：{data['long']} | 做空：{data['short']}"
                )
                print(msg)
                send_telegram_msg(msg)
                return  # 成功抓到今日資料，結束腳本
            else:
                print(f"[{datetime.now(TZ_TW).strftime('%H:%M:%S')}] 今日資料尚未更新，5分鐘後重試...")
        except Exception as e:
            print(f"抓取發生錯誤: {e}")
            
        time.sleep(interval_seconds)
        
    # 若超過設定時間仍未抓到
    send_telegram_msg(f"警告：截至 {datetime.now(TZ_TW).strftime('%H:%M')} 仍未爬取到 {today_str} 的微台指散戶多空比資料。")

if __name__ == "__main__":
    main()
