from playwright.sync_api import sync_playwright
from datetime import datetime
import argparse
import csv
import os
import time

def scrape_titles(keyword: str, timeout_ms: int = 20000, retry: int = 2) -> list[str]:
    url = f"https://www.amazon.co.jp/s?k={keyword}"
    sel = "[data-component-type='s-search-result'] h2 span"

    for attempt in range(retry + 1):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                locale="ja-JP",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                page.wait_for_selector(sel, timeout=timeout_ms)

                elems = page.query_selector_all(sel)
                titles = [e.inner_text().strip() for e in elems if e.inner_text().strip()]

                # 重複除去（順序保持）
                seen = set()
                uniq = []
                for t in titles:
                    if t not in seen:
                        seen.add(t)
                        uniq.append(t)
                return uniq

            except Exception as e:
                os.makedirs("screenshots/error", exist_ok=True)
                os.makedirs("html/error", exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                png = f"screenshots/error/amazon_error_{ts}.png"
                html = f"html/error/amazon_error_{ts}.html"

                try:
                    page.screenshot(path=png, full_page=True)
                    page.content()  # warm up
                    with open(html, "w", encoding="utf-8") as f:
                        f.write(page.content())
                except:
                    pass

                print(f"❌ エラー attempt={attempt+1}/{retry+1}")
                print("内容:", e)
                print("URL:", page.url)
                print("スクショ:", png)
                print("HTML:", html)

                if attempt < retry:
                    time.sleep(2)

            finally:
                browser.close()

    return []

def save_csv(titles: list[str], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name"])
        for t in titles:
            w.writerow([t])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kw", required=True, help="検索キーワード")
    ap.add_argument("--out", default="data/amazon_titles.csv", help="出力CSVパス")
    ap.add_argument("--top", type=int, default=10, help="表示する件数")
    args = ap.parse_args()

    titles = scrape_titles(args.kw)
    print("件数:", len(titles))

    if titles:
        print(f"上位{args.top}件:")
        for t in titles[: args.top]:
            print("-", t)
        save_csv(titles, args.out)
        print("✅ 保存:", args.out)
    else:
        print("取得できず（スクショ/HTMLを確認して原因追跡してね）")

if __name__ == "__main__":
    main()

