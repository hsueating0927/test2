import requests
from bs4 import BeautifulSoup
import json
import time
import random
from dataclasses import dataclass, asdict
from typing import Optional
import os

@dataclass
class ProductPrice:
    item: str
    platform: str
    price: int
    brand: Optional[str] = None
    color: Optional[str] = None
    info: Optional[str] = None

def parse_feebee(html_content: str) -> list[ProductPrice]:
    results = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 飛比目前的商品容器通常在這些 class 裡面
    # 我們改抓所有包含 "item" 關鍵字的 li 或 div
    items = soup.find_all(['li', 'div'], class_=lambda x: x and 'item' in x)
    
    for item in items:
        try:
            # 1. 抓標題：通常在 h3 或具有大標題特徵的 a 標籤
            title_tag = item.find(['h3', 'h2']) or item.select_one('a[title]')
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # 2. 抓價格：飛比現在愛用 .price 或 .item-price
            price_tag = item.select_one('.price') or item.select_one('.item-price')
            if not price_tag:
                continue # 沒價格的通常不是我們要的商品
                
            price_text = price_tag.get_text(strip=True).replace(',', '').replace('$', '').replace('元', '')
            # 處理區間價（只取最小）並過濾非數字
            price_text = price_text.split('~')[0].split('-')[0]
            price_val = "".join(filter(str.isdigit, price_text))
            price = int(price_val) if price_val else 0
            
            # 3. 抓平台：飛比通常標記在 .shop 或 .website-name
            shop_tag = item.select_one('.shop') or item.select_one('.website-name') or item.select_one('.item-shop')
            platform = shop_tag.get_text(strip=True) if shop_tag else "飛比價格"
            
            if title and price > 0:
                results.append(ProductPrice(
                    item=title,
                    platform=platform,
                    price=price
                ))
        except:
            continue
            
    return results

def scrape_feebee(keyword: str, pages: int = 3, output_file: str = "feebee_prices.json"):
    all_products = []
    # 更新 Headers 模擬更像真實瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://feebee.com.tw/",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8"
    }

    for p in range(pages):
        current_page = p + 1
        url = f"https://feebee.com.tw/s/?q={keyword}&page={current_page}"
        print(f"🚀 正在抓取飛比第 {current_page} 頁：{url}")
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            
            if "Robot Check" in res.text:
                print("❌ 被偵測為機器人了！請稍後再試。")
                break
                
            page_products = parse_feebee(res.text)
            
            # 如果這頁沒抓到，嘗試一種更暴力的補救抓法
            if not page_products:
                print("⚠️ 標籤抓取失敗，嘗試暴力掃描...")
                # 這裡是一個備用邏輯，直接抓網頁中所有的 <a> 標籤標題
                for a in BeautifulSoup(res.text, 'html.parser').find_all('a', class_='title'):
                    title = a.get_text(strip=True)
                    # 嘗試從附近的同級標籤找價格
                    price_p = a.find_next(class_='price')
                    if price_p:
                        p_val = "".join(filter(str.isdigit, price_p.get_text()))
                        if p_val:
                            page_products.append(ProductPrice(item=title, platform="飛比補救", price=int(p_val)))

            all_products.extend(page_products)
            print(f"✅ 第 {current_page} 頁成功，目前累計 {len(all_products)} 筆")

            if current_page < pages:
                time.sleep(random.uniform(3, 5)) # 飛比抓得慢一點比較安全
            
        except Exception as e:
            print(f"❌ 出錯: {e}")

    # 存檔
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in all_products], f, ensure_ascii=False, indent=2)
    full_path = os.path.abspath(output_file)
    print(f"\n✨ 任務完成！共存檔 {len(all_products)} 筆。")
    print(f"📍 檔案儲存位置：{full_path}")
if __name__ == "__main__":
    scrape_feebee("iPhone 16", pages=3)