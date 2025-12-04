from ..utils.webdriver import PlaywrightPage
import asyncio, os, re
from datetime import datetime, timedelta
from astrbot.api import logger, AstrBotConfig
from typing import Optional, Dict, Tuple

last_screenshot_time: Dict[int, datetime] = {}

lock = asyncio.Lock()

EVNET_ID_PATTERN = r'event(\d+)'
RANK_PATTERN = r't?(\d+)'
def extract_event_id_rank_from_args(args: str)->Tuple[Optional[None], Optional[None], str]:
    if event_id := re.search(EVNET_ID_PATTERN, args):
        args = args.replace(event_id.group(), '')
        event_id = int(event_id.groups()[0])
    if rank := re.search(RANK_PATTERN, args):
        args = args.replace(rank.group(), '')
        rank = int(rank.groups()[0])
    return event_id, rank, args

async def get_sekairanking_img(config: AstrBotConfig, event_id: Optional[int] = None, rank: Optional[int] = None) -> str:
    global last_screenshot_time, lock
    r"""获取截图的路径"""
    screenshot_path = "data/"
    if event_id is None:
        screenshot_path = f"{screenshot_path}current/"
        event_id = -1
    else:
        screenshot_path = f"{screenshot_path}{event_id}/"
    if rank is None:
        screenshot_path = f"{screenshot_path}overview.png"
    else:
        if rank not in config.all_ranks:
            raise Exception(f"排名 {rank} 无效，支持的排名：{config.all_ranks}")
        screenshot_path = f"{screenshot_path}chart-{rank}.png"
    async with lock:
        if event_id in last_screenshot_time and (datetime.now() < last_screenshot_time[event_id] + timedelta(seconds=config.cache_duration)):
            if os.path.exists(screenshot_path):
                return os.path.abspath(screenshot_path)
        await screenshot_sekairanking_page(config, event_id)
        last_screenshot_time[event_id] = datetime.now()
    return await get_sekairanking_img(config, event_id, rank)

async def screenshot_sekairanking_page(config: AstrBotConfig, event_id: Optional[int] = None):
    url:str = config.base_url
    screenshot_path = "data/"
    if event_id is None:
        screenshot_path = f"{screenshot_path}current/"
    else:
        screenshot_path = f"{screenshot_path}{event_id}/"
        if not url.endswith('/'):
            url += '/'
        url = f"{url}event/{event_id}"
    async with PlaywrightPage() as page:
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=config.timeout*1000)
            loading_overlay_locator = page.locator("#loadingOverlay.loading-overlay.hidden")
            await page.set_viewport_size({"width": config.page_size[0], "height": config.page_size[1]})
            # 等待加载遮罩消失
            await loading_overlay_locator.wait_for(state="attached",timeout=config.timeout*1000)
            # 截图总览
            await page.screenshot(path=f"{screenshot_path}overview.png",full_page=True)
            # 截图单个rank
            for rank in config.all_ranks:
                card_id = f"chart-{rank}"
                card_locator = page.locator(f"xpath=//*[@id='{card_id}']/..")
                await card_locator.screenshot(path=f"{screenshot_path}{card_id}.png")
        except Exception as e:
            logger.error(f"下载图片失败{e}")
            raise
