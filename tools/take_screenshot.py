import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 4000})
        print("Navigating to dashboard...")
        await page.goto("http://localhost:8501")
        
        # Wait for the app to load
        await page.wait_for_selector(".stApp")
        await page.wait_for_timeout(5000)
        
        print("Attempting to click 'Metode og data' tab...")
        try:
            # Find the tab with text "Metode og data"
            tab = page.locator("button[role='tab']", has_text="Metode og data")
            await tab.click()
            
            # Wait for content to render
            await page.wait_for_timeout(5000)
            
            print("Taking screenshot of Metode & data tab...")
            os.makedirs("/Users/andjalis/.gemini/antigravity/brain/5a9e6acb-8030-4474-bc52-480d12a8438b", exist_ok=True)
            screenshot_path = "/Users/andjalis/.gemini/antigravity/brain/5a9e6acb-8030-4474-bc52-480d12a8438b/manual_methodology_screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Success! Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            print(f"Error during interaction: {e}")
            error_path = "/Users/andjalis/.gemini/antigravity/brain/5a9e6acb-8030-4474-bc52-480d12a8438b/manual_error_screenshot.png"
            await page.screenshot(path=error_path, full_page=True)
            print(f"Error screenshot saved to {error_path}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
