import asyncio
import pandas as pd
import os
import subprocess
import traceback
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.ycombinator.com/companies"

async def get_company_links(page, browser):
    url = f"{BASE_URL}?page={page}"
    print(f"Opening company list page: {url}")
    context = await browser.new_context()
    page_obj = await context.new_page()
    print("Navigating to company list page...")
    await page_obj.goto(url)
    print("Waiting 3s for page to load...")
    await page_obj.wait_for_timeout(3000)
    print("Getting company links...")
    try:
        links = await page_obj.eval_on_selector_all(
            "a[href*='/companies/']", "elements => elements.map(el => el.href)"
        )
        print(f"✅ Got {len(links)} company links on page {page}")
    except Exception as e:
        print(f"Failed to get links: {e}")
        links = []
    await context.close()
    return links

async def scrape_company(url, browser):
    print(f"Opening company profile: {url}")
    context = await browser.new_context()
    page = await context.new_page()
    try:
        await page.goto(url)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error loading page {url}: {e}")
        return {}

    async def safe_text(selector):
        try:
            return (await page.locator(selector).first.text_content()).strip()
        except:
            return ""

    async def safe_all_text(selector):
        try:
            return ", ".join([el.strip() for el in await page.locator(selector).all_text_contents()])
        except:
            return ""

    try:
        name = await page.locator("h1").first.text_content()
    except:
        name = ""

    company = {
        "Name": name.strip(),
        "Website": await safe_text("a[data-testid='company-url']"),
        "Description": await safe_text("[data-testid='description']"),
        "Tags": await safe_all_text("a[data-testid='pill']"),
        "Location": await safe_text("[data-testid='location-pill']"),
        "Stage": await safe_text("[data-testid='stage-pill']"),
        "Founders": await safe_all_text("a[data-testid='team-member-name']"),
        "YC URL": url
    }

    await context.close()
    print(f"✅ Scraped: {company['Name']}")
    return company

async def run_scraper(pages=1):
    print("🚀 Starting YC startup scraper with Playwright...")
    all_companies = []
    async with async_playwright() as p:
        for attempt in range(2):
            try:
                print("Launching browser (attempt {} of 2)...".format(attempt + 1))
               browser = await p.chromium.launch(headless=True, timeout=60000)

                print("✅ Browser launched successfully")
                break
            except Exception as e:
                if attempt == 0:
                    print("First launch failed, installing browser binaries...")
                    subprocess.run(["playwright", "install", "chromium"], check=True)
                else:
                    print(f"❌ Failed to launch browser after retry: {e}")
                    return

        for page_num in range(1, pages + 1):
            print(f"🧭 Scraping page {page_num}...")
            try:
                links = await get_company_links(page_num, browser)
                print(f"🔗 Found {len(links)} links on page {page_num}.")
                for link in links:
                    company_data = await scrape_company(link, browser)
                    if company_data:
                        all_companies.append(company_data)
            except Exception as e:
                print(f"⚠️ Error scraping page {page_num}: {e}")
        await browser.close()

    df = pd.DataFrame(all_companies)
    output_path = os.path.join(os.getcwd(), "yc_startups.xlsx")
    df.to_excel(output_path, index=False)
    print(f"✅ Exported {len(df)} companies to: {output_path}")

def main():
    print("✅ Script executed — calling main()...")
    print(">>> Entering run_scraper via asyncio")
    try:
        asyncio.run(run_scraper(pages=1))
    except Exception as e:
        print(f"❌ Script crashed during asyncio.run: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()



