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
    api_url = "https://www.wantgoo.com/investor/retail-indicator/wtm-data"
    
    try:
        with sync_playwright() as p:
            # 啟動真實 Chromium 瀏覽器，開啟過濾驗證防護機制
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 先存取主頁面讓 Cloudflare 通過 Cookie 驗證
            print("正在透過瀏覽器載入玩股網...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000) # 等待 3 秒通過驗證
            
            # 透過瀏覽器內部的 fetch 直接請求 API
            response_json = page.evaluate(f"""
                async () => {{
                    const res = await fetch('{api_url}');
                    return await res.json();
                }}
            """)
            
            browser.close()
            
            if response_json and isinstance(response_json, list) and len(response_json) > 0:
                latest = response_json[0]
                raw_date = str(latest.get("date", "")).replace("-", "/")
                return {
                    "date": raw_date,
                    "price": str(latest.get("price", "")),
                    "long": str(latest.get("long", "")),
                    "short": str(latest.get("short", "")),
                    "ratio": str(latest.get("ratio", ""))
                }
            else:
                print("API 回傳格式不符或無資料")
                return None

    except Exception as e:
        print(f"Playwright 執行失敗: {e}")
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
