import os
import json
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
    blave_url = "https://blave.org/studio/twstock/zh/market/futures_retail_long_short_ratio"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(blave_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 優先方案 1: 解析 Next.js __NEXT_DATA__ SSR 數據
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script and next_data_script.string:
                try:
                    json_obj = json.loads(next_data_script.string)
                    page_props = json_obj.get("props", {}).get("pageProps", {})
                    items = page_props.get("data") or page_props.get("initialData") or []
                    
                    if items and isinstance(items, list):
                        latest = items[0]
                        raw_date = str(latest.get("date", "")).replace("-", "/")
                        
                        # 相容各種可能指稱加權指數/價格的 Key (close, twse, taiex, price, index)
                        p_val = latest.get('close') or latest.get('twse') or latest.get('taiex') or latest.get('price') or latest.get('index') or 0
                        price_str = f"{int(p_val):,}" if isinstance(p_val, (int, float)) and p_val > 0 else str(p_val)
                        
                        long_val = latest.get('long', 0)
                        short_val = latest.get('short', 0)
                        ratio_val = latest.get('ratio', 0)
                        
                        long_str = f"{int(long_val):,}" if isinstance(long_val, (int, float)) else str(long_val)
                        short_str = f"{int(short_val):,}" if isinstance(short_val, (int, float)) else str(short_val)
                        ratio_str = f"{float(ratio_val):+.2f}%" if isinstance(ratio_val, (int, float)) else str(ratio_val)
                        
                        return {
                            "date": raw_date,
                            "price": price_str,
                            "long": long_str,
                            "short": short_str,
                            "ratio": ratio_str
                        }
                except Exception as e:
                    print(f"解析 JSON State 失敗: {e}")

            # 備用方案 2: 直接從 DOM HTML <table> 表格精準提取
            table = soup.find("table")
            if table:
                rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]
                if rows:
                    cols = [cell.text.strip() for cell in rows[0].find_all(["td", "th"])]
                    if len(cols) >= 6:
                        # cols: [0]日期, [1]加權指數, [2]散戶多單, [3]散戶空單, [4]散戶淨部位, [5]散戶多空比
                        return {
                            "date": cols[0].replace("-", "/"),
                            "price": cols[1],
                            "long": cols[2],
                            "short": cols[3],
                            "ratio": cols[5]
                        }

    except Exception as e:
        print(f"爬取過程發生例外錯誤: {e}")
        
    return None

def main():
    today_str = datetime.now(TZ_TW).strftime("%Y/%m/%d")
    print(f"檢查日期: {today_str}")

    try:
        data = fetch_data()
        print(f"爬取結果: {data}")

        # 只要抓到資料，且日期符合今天，即送出推播
        if data and (data['date'] == today_str or data['date'].replace("-", "/") == today_str):
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
            print(f"今日 ({today_str}) 資料尚未更新或日期不符合，結束本次執行。")
    except Exception as e:
        print(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
