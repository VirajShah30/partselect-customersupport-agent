import time
import csv
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.partselect.com"
START_URLS = [
    f"{BASE_URL}/Refrigerator-Parts.htm",
    f"{BASE_URL}/Dishwasher-Parts.htm"
]


def extract_part_links(page):
    links = set()
    part_cards = page.locator("a.nf__part__detail__title")
    count = min(part_cards.count(), 5)  # Limit to 5 for testing
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
            related_wrap = page.locator("div.pd__related-parts-wrap")
            if related_wrap.count() > 0:
                part_anchors = related_wrap.locator("div.pd__related-part a.bold")
                parts = []
                for i in range(part_anchors.count()):
                    name = part_anchors.nth(i).text_content().strip()
                    link = part_anchors.nth(i).get_attribute("href")
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

    def get_rating_from_svg():
        try:
            svg_container = page.locator("div.pd__review-header svg")
            if svg_container.count() > 0:
                svg_element = svg_container.first
                stroke_dasharray = svg_element.get_attribute("stroke-dasharray")
                if stroke_dasharray:
                    filled, total = map(float, stroke_dasharray.split(","))
                    rating = round((filled / total) * 5, 2)
                    return str(rating)
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
        "description": get_description(),
        "rating": get_rating_from_svg()
    }


def save_to_csv(data, filename="data/appliance_parts.csv"):
    keys = data[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


def main():
    all_parts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for start_url in START_URLS:
            print(f"Scraping category page: {start_url}")
            page.goto(start_url, timeout=60000)
            page.wait_for_timeout(3000)

            part_links = extract_part_links(page)
            print(f"Found {len(part_links)} parts")

            for i, link in enumerate(part_links):
                print(f"[{i+1}/{len(part_links)}] Scraping: {link}")
                part_data = extract_part_data(page, link)
                all_parts.append(part_data)
                page.wait_for_timeout(1500)

        browser.close()

    if all_parts:
        save_to_csv(all_parts)
        print("Done. Saved to CSV.")
    else:
        print("No data scraped.")


if __name__ == "__main__":
    main()
