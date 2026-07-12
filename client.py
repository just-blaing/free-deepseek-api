import asyncio
import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .exceptions import ChatNotFoundError, NotAuthenticatedError, ResponseNotFoundError


class DeepSeekClient:
    """
    Неофициальный клиент для chat.deepseek.com через браузерную автоматизацию (Playwright).

    Пример:
        client = DeepSeekClient()
        await client.start()
        answer = await client.ask("привет!")
        await client.close()
    """

    CHAT_URL = "https://chat.deepseek.com/"
    CHAT_LINK_SELECTOR = 'a[href^="/a/chat/s/"]'
    MESSAGE_SELECTOR = ".ds-markdown"

    def __init__(self, auth_path: str = "auth.json", headless: bool = True):
        self.auth_path = auth_path
        self.headless = headless
        self.debug = False

        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def set_debug(self, enable: bool = True) -> None:
        """Включить/выключить debug-логирование в консоль."""
        self.debug = enable

    def _log(self, message: str) -> None:
        if self.debug:
            print(message)

    async def start(self) -> None:
        """Запускает браузер и открывает chat.deepseek.com."""
        self._log("[DEBUG] запуск браузера...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)

        if os.path.exists(self.auth_path):
            self._log("[DEBUG] загрузка сессии из auth.json...")
            self._context = await self._browser.new_context(storage_state=self.auth_path)
        else:
            self._log(f"[DEBUG] файл {self.auth_path} не найден, использую неавторизованную сессию")
            self._context = await self._browser.new_context()

        self._page = await self._context.new_page()
        self._log("[DEBUG] переход на сайт...")
        await self._page.goto(self.CHAT_URL)
        await self._page.wait_for_selector("textarea", timeout=15000)

    async def new_chat(self) -> None:
        """Создаёт новый пустой диалог."""
        self._log("[DEBUG] создание нового чата...")
        await self._page.goto(self.CHAT_URL)
        await self._page.wait_for_selector("textarea", timeout=10000)
        await asyncio.sleep(1)

    async def _parse_sidebar_chats(self) -> list[dict]:
        """Собирает данные о чатах с боковой панели."""
        await self._page.wait_for_selector(self.CHAT_LINK_SELECTOR, timeout=10000)
        chat_elements = await self._page.query_selector_all(self.CHAT_LINK_SELECTOR)

        chats = []
        seen_ids = set()
        for element in chat_elements:
            href = await element.get_attribute("href")
            chat_id = href.split("/")[-1]
            if chat_id in seen_ids:
                continue
            seen_ids.add(chat_id)

            chat_title = (await element.inner_text()).strip()
            chats.append({
                "id": chat_id,
                "title": chat_title,
                "url": f"https://chat.deepseek.com{href}",
            })
        return chats

    async def get_chat_titles(self) -> list[str]:
        """Возвращает список названий всех чатов в боковой панели."""
        chats = await self._parse_sidebar_chats()
        return [chat["title"] for chat in chats]

    async def open_chat_by_title(self, title: str) -> bool:
        """
        Открывает чат по (под)названию, регистронезависимо.
        Возвращает True при успехе, False если чат не найден.
        """
        self._log(f"[DEBUG] ищу чат с названием '{title}'...")
        chats = await self._parse_sidebar_chats()
        target_chat = next(
            (c for c in chats if title.lower() in c["title"].lower()), None
        )

        if not target_chat:
            self._log(f"[DEBUG] чат '{title}' не найден")
            return False

        self._log(f"[DEBUG] чат найден, перехожу на: {target_chat['url']}")
        await self._page.goto(target_chat["url"])
        await self._page.wait_for_selector("textarea", timeout=15000)
        await asyncio.sleep(1.5)
        return True

    async def set_thinking(self, enable: bool = True) -> None:
        """Включает/выключает режим DeepThink (глубокое мышление)."""
        think_span = self._page.locator(
            "//span[text()='Глубокое мышление' or text()='DeepThink']"
        )
        think_btn = self._page.locator("div[aria-pressed]").filter(has=think_span).first
        await think_btn.wait_for(state="visible", timeout=5000)

        is_active = (await think_btn.get_attribute("aria-pressed")) == "true"
        if enable != is_active:
            await think_btn.click()
            self._log(f"[DEBUG] режим thinking {'включён' if enable else 'выключен'}")
        else:
            self._log(f"[DEBUG] режим thinking уже в нужном состоянии (enable={enable})")
        await asyncio.sleep(1)

    async def ask(self, prompt: str, system_prompt: str | None = None, wait_time: int = 20) -> str:
        """
        Отправляет сообщение в текущий чат и возвращает последний ответ модели.

        wait_time - сколько секунд ждать генерации ответа перед чтением DOM.
        Для длинных ответов (особенно с DeepThink) может понадобиться больше времени.
        """
        full_prompt = f"[SYSTEM INSTRUCTION: {system_prompt}]\n\nUSER: {prompt}" if system_prompt else prompt

        textarea_selector = "textarea"
        await self._page.wait_for_selector(textarea_selector, timeout=10000)
        self._log(f"[DEBUG] отправка сообщения: '{prompt[:30]}...'")

        await self._page.fill(textarea_selector, full_prompt)
        await self._page.press(textarea_selector, "Enter")
        await asyncio.sleep(wait_time)

        messages = await self._page.query_selector_all(self.MESSAGE_SELECTOR)
        if not messages:
            raise ResponseNotFoundError("не удалось найти ответ модели в DOM")

        return await messages[-1].inner_text()

    async def close(self) -> None:
        """Закрывает браузер и освобождает ресурсы Playwright."""
        self._log("[DEBUG] закрываю браузер...")
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def __aenter__(self) -> "DeepSeekClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
