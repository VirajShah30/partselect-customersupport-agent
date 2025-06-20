import time
import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://www.partselect.com"


def extract_models_on_page(page, page_num=1):
    model_url = f"{BASE_URL}/Refrigerator-Models.htm?start={page_num}"
    page.goto(model_url, timeout=60000)

    try:
        page.wait_for_selector(".nf__links li a", timeout=10000)
    except:
        print(f"Timeout on page {model_url} — skipping.")
        return []

    model_elements = page.locator(".nf__links li a")

    model_data = []
    count = model_elements.count()
    for i in range(count):
        element = model_elements.nth(i)
        name = element.text_content().strip()
        link = element.get_attribute("href")
        full_link = BASE_URL + link if link.startswith("/") else link
        model_data.append({
            "model_name": name,
            "model_url": full_link
        })
    return model_data


def extract_parts_from_model(page, model):
    part_ids = []
    part_page_num = 1

    while True and part_page_num <= 10:  # Limit to 100 pages to avoid infinite loop
        part_url = f"{model['model_url']}Parts/?start={part_page_num}"
        page.goto(part_url, timeout=60000)

        if "Page Not Found" in page.content() or "Sorry, we couldn't find any parts that matched." in page.content():
            break

        soup = BeautifulSoup(page.content(), "html.parser")
        bold_spans = soup.find_all("span", class_="bold")

        for span in bold_spans:
            if span.get_text(strip=True) == "PartSelect #:":
                parent_div = span.find_parent("div")
                if parent_div:
                    span.extract()
                    part_id = parent_div.get_text(strip=True)
                    part_ids.append(part_id)

        part_page_num += 1


    return {
        "model_name": model["model_name"],
        "part_ids": " | ".join(part_ids) if part_ids else "NA"
    }


def save_streamed_model_part_data(row, file_path="data/model_parts_map_refrigerator.csv"):
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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for page_num in range(1, 2):  # Extend range for more pages
            print(f"\nExtracting models from page {page_num}...")
            models = extract_models_on_page(page, page_num)
            print(f"Found {len(models)} models")

            for i, model in enumerate(models):  # Limit to first 5 models for testing
                print(f"\n[{i+1}/{len(models)}] Processing model: {model['model_name']}")
                part_record = extract_parts_from_model(page, model)
                save_streamed_model_part_data(part_record)
                time.sleep(0.5)

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
