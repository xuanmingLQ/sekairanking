from ..utils.webdriver import PlaywrightPage
import asyncio, os
from datetime import datetime, timedelta
from astrbot.api import logger, AstrBotConfig

last_screenshot_time: datetime | None = None

lock = asyncio.Lock()

async def get_sekairanking_img(config: AstrBotConfig, rank: int | None = None):
    global last_screenshot_time, lock
    r"""获取截图的路径"""
    if rank == None:
        screenshot_path = "data/overview.png"
    else:
        if rank not in config.all_ranks:
            raise Exception(f"排名 {rank} 无效，支持的排名：{config.all_ranks}")
        screenshot_path = f"data/chart-{rank}.png"
    async with lock:
        if last_screenshot_time is not None and datetime.now() < last_screenshot_time + timedelta(seconds=config.cache_duration):
            if os.path.exists(screenshot_path):
                return os.path.abspath(screenshot_path)
        await screenshot_sekairanking_page(config)
        last_screenshot_time = datetime.now()
    return get_sekairanking_img(config, rank)

async def screenshot_sekairanking_page(config: AstrBotConfig,):
    async with PlaywrightPage() as page:
        try:
            await page.goto(config.base_url, wait_until='domcontentloaded', timeout=config.timeout*1000)
            loading_overlay_locator = page.locator("#loadingOverlay.loading-overlay.hidden")
            await page.set_viewport_size({"width": config.page_size[0], "height": config.page_size[1]})
            # 等待加载遮罩消失
            await loading_overlay_locator.wait_for(state="attached",timeout=config.timeout*1000)
            # 截图总览
            await page.screenshot(path="data/overview.png",full_page=True)
            # 截图单个rank
            for rank in config.all_ranks:
                card_id = f"chart-{rank}"
                card_locator = page.locator(f"xpath=//*[@id='{card_id}']/..")
                await card_locator.screenshot(path=f"data/{card_id}.png")
        except Exception as e:
            logger.error(f"下载图片失败{e}")
            raise
