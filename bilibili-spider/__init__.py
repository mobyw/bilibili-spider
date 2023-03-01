import asyncio
import json
from pathlib import Path

from loguru import logger
from spider import Spider


def get_config() -> dict:
    if not Path("config.json").exists():
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "account_list": [114514, 1919810],
                    "proxy": False,
                    "proxy_api": "",
                    "cookie": "",
                    "data_dir": "data",
                    "video_limit": 0,
                    "comment_limit": 0,
                    "comment_reply": False,
                },
                f,
                indent=4,
            )
        logger.error("Config file not found, please fill in the config file.")
        exit(0)
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


async def main() -> None:
    config = get_config()
    s = Spider(config)
    await s.init()
    await s.spider_all()


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt")
        exit(0)
