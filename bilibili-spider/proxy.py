import random
from typing import Optional

import aiohttp
from loguru import logger

proxy_index = 0
proxy_list = []


async def get_proxy_list(proxy_api):
    """
    获取代理列表
    """
    global proxy_list
    logger.info("Getting proxies...")
    async with aiohttp.ClientSession() as session:
        async with session.get(proxy_api) as resp:
            proxy_list = await resp.text()
            proxy_list = proxy_list.split("<br/>")
            proxy_list = [proxy for proxy in proxy_list if proxy != ""]
            logger.info(
                "Got proxies: "
                + str(proxy_list)
                + "\n"
                + str(len(proxy_list))
                + " proxies in total."
            )


async def check_proxy_validity(proxy: str) -> bool:
    """
    检查代理是否有效
    """
    if not proxy.startswith("http"):
        proxy = "http://" + proxy

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.bilibili.com/x/v2/reply/main", proxy=proxy, timeout=5
            ) as resp:
                if resp.status == 200:
                    logger.success("Proxy " + proxy + " is valid.")
                    return True
                else:
                    logger.warning("Proxy " + proxy + " is invalid.")
                    return False
    except Exception:
        logger.warning("Proxy " + proxy + " is invalid.")
        return False


async def check_proxy_list():
    """
    检查代理列表中的代理是否有效
    """
    global proxy_list
    logger.info("Checking proxies...")
    proxy_list = [proxy for proxy in proxy_list if await check_proxy_validity(proxy)]
    logger.info(
        "Valid proxies: "
        + str(proxy_list)
        + "\n"
        + str(len(proxy_list))
        + " proxies in total."
    )


async def get_random_proxy() -> Optional[str]:
    """
    随机获取一个代理
    """
    global proxy_list
    if not proxy_list:
        return None
    proxy = random.choice(proxy_list)
    if not proxy.startswith("http"):
        proxy = "http://" + proxy
    return proxy


async def get_next_proxy() -> Optional[str]:
    """
    顺序获取一个代理
    """
    global proxy_list
    global proxy_index
    proxy = proxy_list[proxy_index]
    proxy_index += 1
    proxy_index %= len(proxy_list)
    if not proxy.startswith("http"):
        proxy = "http://" + proxy
    return proxy
