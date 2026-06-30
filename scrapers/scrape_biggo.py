import requests
import json
import time
import random
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ProductPrice:
    item: str
    platform: str
    price: int
    brand: Optional[str] = None
    color: Optional[str] = None
    info: Optional[str] = None

def parse_products(ssr_data: dict) -> list[ProductPrice]:
    results = []
    for item in ssr_data.get("list", []):
        title = item.get("title", "")
        store = item.get("store", {})
        platform = store.get("name", "") or item.get("store_title", "")
        try:
            price = int(item.get("current_price") or item.get("price", 0))
        except (ValueError, TypeError):
            price = 0

        color = None
        for c in ["黑色","白色","藍色","紅色","紫色","綠色","黃色","粉色","金色","銀色"]:
            if c in title:
                color = c
                break

        info_parts = []
        if item.get("is_cashback"):
            info_parts.append(f"回饋:{item.get('rate_desc','')}")
        if item.get("discount_info"):
            info_parts.append(f"折扣:{item['discount_info']}")

        results.append(ProductPrice(
            item=title,
            platform=platform,
            price=price,
            color=color,
            info="、".join(info_parts) if info_parts else None,
        ))
    return results

def scrape_biggo(keyword: str, pages: int = 5, output_file: str = "iphone16_prices.json"):
    all_products = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    for p in range(pages):
        current_page = p + 1
        url = f"https://biggo.com.tw/s/{keyword}/?p={current_page}"
        print(f"🚀 正在抓取第 {current_page} 頁：{url}")
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8' # 【解決亂碼關鍵 1】強制使用 UTF-8 解碼
            content = res.text
            
            # 修正某些特殊符號導致的解析問題
            content_clean = content.replace('\\"', '"').replace('\\\\', '\\')
            
            idx = content_clean.find('"ssrData"')
            if idx == -1:
                print(f"⚠️ 第 {current_page} 頁找不到資料")
                continue

            start = content_clean.find('{', idx)
            depth = 0
            end = start
            for i, ch in enumerate(content_clean[start:], start):
                if ch == '{': depth += 1
                elif ch == '}': depth -= 1
                if depth == 0:
                    end = i
                    break
            
            # 【解決亂碼關鍵 2】使用更穩定的 JSON 解析
            ssr_data = json.loads(content_clean[start:end+1])
            page_products = parse_products(ssr_data)
            all_products.extend(page_products)
            
            print(f"✅ 第 {current_page} 頁成功，抓到 {len(page_products)} 筆")

            if current_page < pages:
                sleep_time = random.uniform(2, 4)
                print(f"☕ 休息 {sleep_time:.1f} 秒...")
                time.sleep(sleep_time)
            
        except Exception as e:
            print(f"❌ 第 {current_page} 頁出錯: {e}")

    # 去重
    seen = set()
    unique = []
    for prod in all_products:
        key = (prod.item, prod.platform, prod.price)
        if key not in seen:
            seen.add(key)
            unique.append(prod)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in unique], f, ensure_ascii=False, indent=2)

    print(f"\n✨ 任務圓滿完成！總共儲存 {len(unique)} 筆資料到 {output_file}")

if __name__ == "__main__":
    # 可以隨意更改關鍵字和頁數
    scrape_biggo("iPhone 16", pages=5, output_file="iphone16_prices.json")