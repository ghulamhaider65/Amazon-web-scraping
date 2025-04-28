from playwright.sync_api import sync_playwright
import pandas as pd
import time

def open_amazon(page):
    url = 'https://www.amazon.com/s?k=headphones&ref=nb_sb_noss'
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector("div.s-main-slot div[data-asin][data-component-type='s-search-result']", timeout=10000)
    print("Products are now visible on page.")
    time.sleep(5)

def scrap_products(page):
    products = []
    product_blocks = page.query_selector_all("div.s-main-slot div[data-asin][data-component-type='s-search-result']")

    print(f"🛒 Found {len(product_blocks)} products.")

    for block in product_blocks:
        h2_element = block.query_selector("h2 span")
        title = h2_element.inner_text().strip() if h2_element else "N/A"

        link_element = block.query_selector("a.a-link-normal.s-line-clamp-2")
        link = "https://www.amazon.com" + link_element.get_attribute('href') if link_element else "N/A"

        price_element = block.query_selector("span.a-price > span.a-offscreen")
        if not price_element:
            price_element = block.query_selector("span.a-color-base")
        price = price_element.inner_text().strip() if price_element else "N/A"

        rating_element = block.query_selector("span.a-icon-alt")
        rating = rating_element.inner_text().strip() if rating_element else "N/A"

        products.append({
            'Title': title,
            'Price': price,
            'Rating': rating,
            'Link': link,
        })

    return products

def go_to_next_page(page):
    next_button = page.query_selector('a.s-pagination-next')
    if next_button:
        print("Going to next page...")
        next_button.click()
        time.sleep(5)
        page.wait_for_selector("div.s-main-slot div[data-asin][data-component-type='s-search-result']", timeout=15000)
        return True
    else:
        print("No next page. Finished scraping.")
        return False

def save_to_csv(products):
    df = pd.DataFrame(products)
    df.to_csv('products.csv', index=False)
    print("Data saved successfully to products.csv")

def main():
    all_products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
        ])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            java_script_enabled=True,
            extra_http_headers={
                "accept-language": "en-US,en;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "upgrade-insecure-requests": "1",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "sec-fetch-site": "none",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
            }
        )
        page = context.new_page()

        open_amazon(page)

        page_count = 0
        max_pages = 40

        while True:
            products = scrap_products(page)
            all_products.extend(products)

            page_count += 1
            if page_count >= max_pages:
                print(f"Reached max pages limit: {max_pages}")
                break

            if not go_to_next_page(page):
                break

        save_to_csv(all_products)
        browser.close()

if __name__ == "__main__":
    main()

