
from playwright.async_api import (
    async_playwright, 
    Browser, 
    Playwright, 
    BrowserType, 
    BrowserContext, 
    Page,
)
import os
from astrbot.api import logger

_playwright_instance: Playwright | None = None
_browser_type: BrowserType | None = None
browser: Browser | None = None
class PlaywrightPage:
    """
    异步上下文管理器，用于管理 Playwright 浏览器实例队列。
    """
    def __init__(self, context_options: dict | None = None):
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.context_options: dict = context_options if context_options is not None else { 
                'locale': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            }

    async def __aenter__(self) -> Page:
        global _playwright_instance, _browser_type, browser
        
        if _playwright_instance is None:
            _playwright_instance = await async_playwright().start()
            _browser_type = _playwright_instance.chromium
            
            if os.system("rm -rf /tmp/rust_mozprofile*") != 0:
                logger.error(f"清空WebDriver临时文件失败")
            
            browser = await _browser_type.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox'] 
            )
            logger.info(f"初始化 Playwright Browser 成功")
            pass
            
        self.context = await browser.new_context(**self.context_options)
        self.page = await self.context.new_page()
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        global browser
        # 关闭上下文，自动清理
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                logger.error(f"关闭 Playwright Page 失败 {e}")
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.error(f"关闭 Playwright Context 失败 {e}")
        self.page = None
        self.context = None
        return False
    @classmethod
    async def stop(cls):
        global browser, _playwright_instance
        if browser is not None:
            try:
                await browser.close()
                logger.info("Playwright Browser 已关闭。")
            except Exception as e:
                logger.error(f"关闭 Playwright Browser 失败: {e}")
        if _playwright_instance is not None:
            try:
                await _playwright_instance.stop()
                logger.info("Playwright 实例已停止。")
            except Exception as e:
                logger.error(f"停止 Playwright 实例失败: {e}")