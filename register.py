import asyncio
import time
from playwright.async_api import async_playwright


async def _register() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://chat.deepseek.com/")
        input("войди в свой акк и нажми enter в консоли после входа")
        # кстати, можно войти на пк и потом юзать на телефоне в termux (к примеру)
        # но лучше не юзать это в коммерческих целях - сессию могут забанить за такое
        # (ну или на крайняк юзайте официальный api)
        await context.storage_state(path="auth.json")
        await browser.close()
        print("сессия сохранена в auth.json!")
        time.sleep(3)


def main() -> None:
    asyncio.run(_register())
    
if __name__ == "__main__":
    main()
