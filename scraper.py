import os
import requests
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

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
    url = "https://www.wantgoo.com/futures/retail-indicator/wtm"
    
    try:
        with sync_playwright() as p:
            # 啟動真實 Chromium 瀏覽器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print("正在透過瀏覽器載入玩股網頁面...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待表格渲染完成
            page.wait_for_selector("table", timeout=15000)
            
            # 直接從頁面提取第一列表格數據
            first_row = page.locator("table tbody tr").first
            cols = first_row.locator("td").all_inner_texts()
            
            browser.close()
            
            if len(cols) >= 5:
                return {
                    "date": cols[0].strip(),
                    "price": cols[1].strip(),
                    "long": cols[2].strip(),
                    "short": cols[3].strip(),
                    "ratio": cols[4].strip()
                }
            else:
                print("表格欄位不足")
                return None

    except Exception as e:
        print(f"Playwright 抓取表格失敗: {e}")
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
