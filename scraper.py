def fetch_data():
    # 修正後的正確 API 網址與完整的 HTTP Headers
    url = "https://blave.org/api/studio/twstock/zh/market/futures-retail-long-short-ratio?symbol=wtm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://blave.org/studio/twstock/zh/market/futures_retail_long_short_ratio"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"請求失敗，HTTP 狀態碼: {response.status_code}")
            return None

        json_data = response.json()
        
        # 取得列表的第一筆資料 (最新日期的資料)
        items = json_data.get("data", []) if isinstance(json_data, dict) else json_data
        if items and isinstance(items, list):
            latest = items[0]
            
            # API 回傳日期格式為 "2026-10-02"，轉為 "2026/10/02"
            raw_date = str(latest.get("date", "")).replace("-", "/")
            
            price = f"{latest.get('close', 0):,}" if latest.get('close') else str(latest.get('price', ''))
            long_cnt = f"{latest.get('long', 0):,}" if latest.get('long') else str(latest.get('long', ''))
            short_cnt = f"{latest.get('short', 0):,}" if latest.get('short') else str(latest.get('short', ''))
            ratio = f"{latest.get('ratio', 0):+.2f}%" if latest.get('ratio') is not None else str(latest.get('ratio', ''))
            
            return {
                "date": raw_date,
                "price": price,
                "long": long_cnt,
                "short": short_cnt,
                "ratio": ratio
            }
        else:
            print("API 回傳資料結構為空")
    except Exception as e:
        print(f"解析發生錯誤: {e}")
        
    return None
