import time
import csv
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.partselect.com"
PART_CATEGORY_URL = f"{BASE_URL}/Dishwasher-Parts.htm"

def get_part_type_links(page):
    page.goto(PART_CATEGORY_URL, timeout=60000)
    page.wait_for_selector("#ShopByPartType", timeout=10000)
    part_type_links = []
    links = page.locator("#ShopByPartType + ul a")
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href")
        if href:
            full_link = BASE_URL + href if href.startswith("/") else href
            part_type_links.append(full_link)
    return part_type_links

def extract_all_part_links(page, category_url):
    page.goto(category_url, timeout=60000)
    page.wait_for_timeout(2000)
    links = set()
    part_cards = page.locator("a.nf__part__detail__title")
    count = part_cards.count()
    for i in range(count):
        href = part_cards.nth(i).get_attribute("href")
        if href and "/PS" in href:
            links.add(BASE_URL + href if href.startswith("/") else href)
    return list(links)

def extract_part_data(page, url):
    page.goto(url, timeout=60000)
    page.wait_for_selector("h1", timeout=10000)

    def safe_get(selector):
        try:
            content = page.locator(selector)
            if content.count() > 0:
                return content.first.text_content().strip()
            return "N/A"
        except:
            return "N/A"

    def get_video_url():
        try:
            yt_div = page.locator("div.yt-video")
            if yt_div.count() > 0:
                yt_id = yt_div.first.get_attribute("data-yt-init")
                if yt_id:
                    return f"https://www.youtube.com/watch?v={yt_id}"
            return "N/A"
        except:
            return "N/A"

    def get_text_after(header_text):
        blocks = page.locator("div.col-md-6.mt-3")
        for i in range(blocks.count()):
            text = blocks.nth(i).text_content()
            if header_text.lower() in text.lower():
                stripped = text.split(":", 1)[-1].strip()
                return ", ".join([t.strip() for t in stripped.split(",")])
        return "N/A"

    def get_install_info():
        difficulty = "N/A"
        time_required = "N/A"
        info_block = page.locator("div.d-flex.flex-lg-grow-1.col-lg-7.col-12.justify-content-lg-between.mt-lg-0.mt-2")
        if info_block.count() > 0:
            items = info_block.first.locator(".d-flex p")
            if items.count() >= 2:
                difficulty = items.nth(0).text_content().strip()
                time_required = items.nth(1).text_content().strip()
        return difficulty, time_required

    def get_related_parts():
        try:
            related_wrap = page.locator("div.pd__related-part-wrap")
            if related_wrap.count() > 0:
                part_divs = related_wrap.locator("div.pd__related-part")
                parts = []
                for i in range(part_divs.count()):
                    a_tag = part_divs.nth(i).locator("a").first
                    name = a_tag.text_content().strip()
                    link = a_tag.get_attribute("href")
                    full_link = BASE_URL + link if link.startswith("/") else link
                    parts.append(f"{name} ({full_link})")
                return " | ".join(parts) if parts else "N/A"
            return "N/A"
        except:
            return "N/A"

    def get_replacement_parts():
        try:
            all_blocks = page.locator("div.col-md-6.mt-3")
            for i in range(all_blocks.count()):
                text = all_blocks.nth(i).text_content()
                if "replaces these:" in text.lower():
                    return text.split("replaces these:", 1)[-1].strip()
            return "N/A"
        except:
            return "N/A"

    def get_description():
        try:
            desc = page.locator("div[itemprop='description']")
            if desc.count() > 0:
                return desc.first.text_content().strip()
            return "N/A"
        except:
            return "N/A"

    difficulty, install_time = get_install_info()

    return {
        "url": url,
        "title": safe_get("h1"),
        "part_id": safe_get("span[itemprop='productID']"),
        "brand": safe_get("span[itemprop='brand'] span[itemprop='name']"),
        "availability": safe_get("span[itemprop='availability']"),
        "price": safe_get("span.price.pd__price span.js-partPrice"),
        "symptoms": get_text_after("symptoms"),
        "product_types": get_text_after("products"),
        "installation_difficulty": difficulty,
        "installation_time": install_time,
        "related_parts": get_related_parts(),
        "replacement_parts": get_replacement_parts(),
        "video_url": get_video_url(),
        "description": get_description()
    }

def save_streamed_data(row, file_path="data/appliance_parts_dishwasher.csv"):
    file_exists = False
    try:
        with open(file_path, mode="r", encoding="utf-8") as _:
            file_exists = True
    except:
        pass

    with open(file_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def scrape_part_type_page(browser, part_type_url):
    context = browser.new_context()
    page = context.new_page()
    part_links = extract_all_part_links(page, part_type_url)
    print(f"Found {len(part_links)} parts in: {part_type_url}")

    for i, link in enumerate(part_links):
        print(f"[{i+1}/{len(part_links)}] Scraping: {link}")
        part_data = extract_part_data(page, link)
        save_streamed_data(part_data)
        page.wait_for_timeout(500)

    context.close()

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Fetching all part type links...")
        part_type_links = get_part_type_links(page)
        context.close()

        print(f"Found {len(part_type_links)} part type pages")
        for i, link in enumerate(part_type_links):
            print(f"\nProcessing part type {i+1}/{len(part_type_links)}: {link}")
            scrape_part_type_page(browser, link)

        browser.close()

if __name__ == "__main__":
    main()
