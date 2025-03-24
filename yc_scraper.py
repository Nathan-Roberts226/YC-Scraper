# yc_scraper.py
# Fully turnkey YC startup scraper using Playwright. Ready for GitHub upload and Render deployment.

import asyncio
import pandas as pd
import os
import subprocess
from playwright.async_api import async_playwright

BASE_URL = "https://www.ycombinator.com/companies"

async def get_company_links(page, browser):
    url = f"{BASE_URL}?page={page}"
    context = await browser.new_context()
    page_obj = await context.new_page()
    await page_obj.goto(url)
    await page_obj.wait_for_timeout(5000)  # wait 5 seconds for full JS rendering
    links = await page_obj.eval_on_selector_all(
        "a[href*='/companies/']", "elements => elements.map(el => el.href)"
    )
    await context.close()
    return links

async def scrape_company(url, browser):
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url)
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(3000)  # give JS more time to render content

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
    return company

async def run_scraper(pages=1):
    print("Starting YC startup scraper with Playwright...")
    all_companies = []
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except:
            print("Missing browser binaries. Installing...")
            subprocess.run(["playwright", "install", "chromium"], check=True)
            browser = await p.chromium.launch(headless=True)

        for page_num in range(1, pages + 1):
            print(f"Scraping page {page_num}...")
            links = await get_company_links(page_num, browser)
            for link in links:
                print(f" - Scraping: {link}")
                company_data = await scrape_company(link, browser)
                all_companies.append(company_data)
        await browser.close()

    df = pd.DataFrame(all_companies)
    output_path = os.path.join(os.getcwd(), "yc_startups.xlsx")
    df.to_excel(output_path, index=False)
    print(f"✅ Exported {len(df)} companies to: {output_path}")

if __name__ == "__main__":
    asyncio.run(run_scraper(pages=1))
