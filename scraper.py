import os
import requests
from bs4 import BeautifulSoup
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
    url = "https://blave.org/studio/twstock/zh/market/futures_retail_long_short_ratio"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"請求失敗，HTTP 狀態碼: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print("找不到表格")
            return None

        # 找到 tbody 中的第一列 (最新日期的資料)
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
        
        if rows:
            # 抓取第一列中所有的 th 及 td 子元素
            cols = [cell.text.strip() for cell in rows[0].find_all(['th', 'td'])]
            
            # 欄位依序為：日期、加權指數、散戶多單、散戶空單、散戶淨部位、散戶多空比
            if len(cols) >= 6:
                date_formatted = cols[0].replace("-", "/")
                return {
                    "date": date_formatted,
                    "price": cols[1],
                    "long": cols[2],
                    "short": cols[3],
                    "ratio": cols[5]
                }
            else:
                print(f"欄位數量不足，實際抓到 {len(cols)} 個欄位: {cols}")
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
