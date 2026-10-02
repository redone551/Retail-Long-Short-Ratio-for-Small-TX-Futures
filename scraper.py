import os
import cloudscraper
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
        # 使用普通的 requests 或 cloudscraper 皆可發送 Telegram
        scraper = cloudscraper.create_scraper()
        res = scraper.post(url, data=payload, timeout=10)
        print(f"Telegram API 回應: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"發送通知失敗: {e}")

def fetch_data():
    url = "https://www.wantgoo.com/futures/retail-indicator/wtm"
    
    # 建立 cloudscraper 實例，模擬真實瀏覽器挑戰驗證
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"網頁請求失敗，HTTP 狀態碼: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print("找不到資料表格")
            return None

        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
        for row in rows:
            cols = [td.text.strip() for td in row.find_all(['td', 'th'])]
            if len(cols) >= 5:
                return {
                    "date": cols[0].strip(),
                    "price": cols[1].strip(),
                    "long": cols[2].strip(),
                    "short": cols[3].strip(),
                    "ratio": cols[4].strip()
                }
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
