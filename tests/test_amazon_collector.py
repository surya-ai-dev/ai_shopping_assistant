import asyncio

from playwright.async_api import async_playwright

from src.collectors.amazon import AmazonCollector
from src.core.request_manager import RequestManager
from src.collectors.amazon import AmazonParser



async def main():
    url = "https://www.amazon.in/gp/aw/d/B0GSWFSHQ4/?_encoding=UTF8&pd_rd_plhdr=t&aaxitk=7acc5d88e46c3b10416a72c546642cb4&hsa_cr_id=0&qid=1785332545&sr=1-1-e0fa1fdd-d857-4087-adda-5bd576b25987&i=aps&aref=A4ZPMfAGZF&ref_=sbx__sbtcd_asin_0_img&pd_rd_w=PxobJ&content-id=amzn1.sym.c0c4f4ed-4ecc-4626-b0b0-d428311a6244%3Aamzn1.sym.c0c4f4ed-4ecc-4626-b0b0-d428311a6244&pf_rd_p=c0c4f4ed-4ecc-4626-b0b0-d428311a6244&pf_rd_r=61RAJYCDCYHDDRV902A5&pd_rd_wg=n8xQs&pd_rd_r=131df0e0-3688-4341-abeb-0c62cbe1f3b3&th=1"   # Any valid Amazon product URL

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        page = await browser.new_page()

        collector = AmazonCollector(
            request_manager=RequestManager()
        )

        print("Opening Amazon page...")

        response = await collector.fetch_page(page, url)

        if response:
            print(f"Status Code: {response.status}")

        html = await page.content()

        parser = AmazonParser()

        product = await parser.parse(
            html_content=html,
            url=url
        )

        print(product)

        print(f"HTML Length: {len(html)}")

        with open("amazon.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("Saved HTML to amazon.html")

        print("Page Title:", await page.title())

        await browser.close()


asyncio.run(main())