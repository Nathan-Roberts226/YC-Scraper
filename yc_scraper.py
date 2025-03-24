import requests
import pandas as pd
from bs4 import BeautifulSoup
import os

BASE_URL = "https://www.ycombinator.com/companies"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_company_links(page=1):
    url = f"{BASE_URL}?page={page}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.select("a.styles-module__company___nPzU4")
    return ["https://www.ycombinator.com" + link['href'] for link in links]

def scrape_company(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    def try_select(selector, index=None):
        try:
            if index is not None:
                return soup.select(selector)[index].text.strip()
            return soup.select_one(selector).text.strip()
        except:
            return ""

    def try_select_all(selector):
        try:
            return [el.text.strip() for el in soup.select(selector)]
        except:
            return []

    return {
        "Name": try_select("h1"),
        "Website": try_select("a[href^='http']"),
        "Description": try_select("div.styles-module__description___HUIeN"),
        "Tags": ", ".join(try_select_all("a.styles-module__pill___2I2W_")),
        "Location": try_select("div.styles-module__metadata___zyzCz > span", 0),
        "Stage": try_select("div.styles-module__metadata___zyzCz > span", 1),
        "Founders": ", ".join(try_select_all("a.styles-module__founder___z_w_r")),
        "YC URL": url
    }

def main(pages=2):
    print("Starting YC startup scraper...")
    all_companies = []
    for page in range(1, pages + 1):
        print(f"Scraping page {page}...")
        links = get_company_links(page)
        for link in links:
            print(f" - Scraping: {link}")
            data = scrape_company(link)
            all_companies.append(data)

    df = pd.DataFrame(all_companies)
    output_path = os.path.join(os.getcwd(), "yc_startups.xlsx")
    df.to_excel(output_path, index=False)
    print(f"✅ Exported {len(df)} companies to: {output_path}")

if __name__ == "__main__":
    main(pages=2) 
