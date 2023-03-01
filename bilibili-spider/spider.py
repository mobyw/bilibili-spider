import json
import re
import time
from asyncio import sleep
from pathlib import Path
from random import randint
from typing import Any, Optional, Union

import aiohttp
from loguru import logger
from proxy import check_proxy_list, get_proxy_list, get_random_proxy

api_person_info = "https://api.bilibili.com/x/space/acc/info?mid={}"
api_person_video_page = "https://api.bilibili.com/x/space/arc/search?mid={}&pn={}"
api_video_comment_page = (
    "https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn={}&type=1&oid={}"
)
api_video_comment_reply_page = (
    "https://api.bilibili.com/x/v2/reply/reply?jsonp=jsonp&pn={}&type=1&oid={}&root={}"
)


class Spider:
    config = {
        "account_list": [],
        "proxy": False,
        "proxy_api": "",
        "cookie": "",
        "data_dir": "data",
        "video_limit": 0,
        "comment_limit": 0,
        "comment_reply": False,
    }

    data_dir: Path = Path("data")
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
    }

    def __init__(
        self,
        config: dict,
    ) -> None:
        self.config = config

    @staticmethod
    def get_attr(dict: dict, key: str, default: Any = None) -> Any:
        """获取字典中的值，如果不存在则返回默认值"""
        if key in dict:
            return dict[key]
        else:
            return default

    @staticmethod
    def is_valid_path(path):
        """检查路径是否有效"""
        if not isinstance(path, str):
            return False
        pattern = re.compile(r"^[\w\-.]+$")
        return bool(pattern.match(path))

    async def check_config(self) -> bool:
        """检查配置是否正确"""
        if not isinstance(self.config, dict):
            logger.error("Config must be a dict.")
            return False
        account_list = self.get_attr(self.config, "account_list")
        proxy = self.get_attr(self.config, "proxy")
        proxy_api = self.get_attr(self.config, "proxy_api")
        data_dir = self.get_attr(self.config, "data_dir")
        video_limit = self.get_attr(self.config, "video_limit")
        comment_limit = self.get_attr(self.config, "comment_limit")
        comment_reply = self.get_attr(self.config, "comment_reply")
        if account_list is None:
            logger.error("Account list is not set.")
            return False
        if not isinstance(account_list, list):
            logger.error("Account list must be a list.")
            return False
        if proxy is None:
            self.config["proxy"] = False
        elif proxy and (proxy_api is None or proxy_api == ""):
            logger.error("Proxy API is not set.")
            return False
        else:
            self.config["proxy"] = False
        if data_dir is None or data_dir == "":
            self.config["data_dir"] = "data"
        elif not self.is_valid_path(data_dir):
            logger.error("Data dir is not valid.")
            return False
        if video_limit is None:
            self.config["video_limit"] = 0
        elif not isinstance(video_limit, int):
            logger.error("Video limit must be an integer.")
            return False
        if comment_limit is None:
            self.config["comment_limit"] = 0
        elif not isinstance(comment_limit, int):
            logger.error("Comment limit must be an integer.")
            return False
        if comment_reply is None:
            self.config["comment_reply"] = False
        elif not isinstance(comment_reply, bool):
            logger.error("Comment reply must be a boolean.")
            return False
        return True

    async def init(self) -> None:
        """初始化"""
        logger.info("Initializing...")
        check = await self.check_config()
        if not check:
            logger.error("Config error.")
            exit(0)
        self.data_dir = Path(self.config["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "users").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "videos").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "comments").mkdir(parents=True, exist_ok=True)
        if self.config["proxy"]:
            logger.info("Using proxy.")
            await get_proxy_list(self.config["proxy_api"])
            await check_proxy_list()
        if self.get_attr(self.config, "cookie") is not None:
            self.headers["Cookie"] = self.config["cookie"]

    async def request(self, url: str) -> Optional[str]:
        """请求"""
        proxy = get_random_proxy() if self.config["proxy"] else None
        try:
            async with aiohttp.ClientSession() as session:
                if self.config["proxy"] and proxy:
                    async with session.get(
                        url, headers=self.headers, proxy=proxy
                    ) as resp:
                        return await resp.text()
                else:
                    async with session.get(url, headers=self.headers) as resp:
                        return await resp.text()
        except Exception as e:
            logger.error(f"Request error: {e}")
            logger.error(f"Url: {url}")
            logger.exception(e)
            return None

    async def get_user_info(self, mid: int) -> Optional[dict]:
        """获取用户信息"""
        if not self.config["proxy"]:
            await sleep(randint(1, 3))
        url = api_person_info.format(mid)
        res = await self.request(url)
        if not res:
            return None
        try:
            info = json.loads(res)
            return info["data"]
        except Exception as e:
            logger.error(f"Get user info error: {e}")
            logger.error(f"User id: {mid}")
            logger.error(f"Response: {res}")
            logger.exception(e)
            return None

    async def get_user_video_list(self, mid: int) -> list:
        """获取用户视频列表"""
        page = 1
        video_list = []
        while True:
            index = int(page / 2) % 4
            list = ["\\", "|", "/", "-"]
            print(f"\r{list[index]}\r", end="")
            if not self.config["proxy"]:
                if page % 2 == 0:
                    await sleep(randint(1, 3))
            url = api_person_video_page.format(mid, page)
            res = await self.request(url)
            if not res:
                break
            info = json.loads(res)
            if info["data"]["list"]["vlist"]:
                for video_item in info["data"]["list"]["vlist"]:
                    video_list.append(video_item)
                page += 1
            else:
                break
        return video_list

    async def get_video_comment_list(self, aid: int) -> list:
        """获取视频评论列表"""
        logger.info("Start spidering video " + str(aid))
        page = 1
        comment_list = []
        while True:
            index = int(page / 2) % 4
            list = ["\\", "|", "/", "-"]
            print(f"\r{list[index]}\r", end="")
            if not self.config["proxy"]:
                if page % 2 == 0:
                    await sleep(randint(1, 3))
            url = api_video_comment_page.format(page, aid)
            res = await self.request(url)
            if not res:
                break
            info = json.loads(res)
            if info["data"]["replies"]:
                for comment_item in info["data"]["replies"]:
                    comment_list.append(comment_item)
                    if (
                        self.config["comment_limit"] != 0
                        and len(comment_list) >= self.config["comment_limit"]
                    ):
                        return comment_list
                page += 1
            else:
                break
        if not self.config["comment_reply"]:
            return comment_list
        for comment_item in comment_list:
            if comment_item["replies"]:
                rpid = comment_item["rpid"]
                page = 1
                while True:
                    index = int(page / 2) % 4
                    list = ["\\", "|", "/", "-"]
                    print(f"\r{list[index]}\r", end="")
                    if not self.config["proxy"]:
                        if page % 2 == 0:
                            await sleep(randint(1, 3))
                    url = api_video_comment_reply_page.format(page, aid, rpid)
                    res = await self.request(url)
                    if not res:
                        break
                    info = json.loads(res)
                    if info["data"]["replies"]:
                        for sub_comment_item in info["data"]["replies"]:
                            comment_list.append(sub_comment_item)
                        page += 1
                    else:
                        break
        return comment_list

    async def save_data(
        self, data: Union[dict, list], folder: str, file_name: str
    ) -> None:
        """保存数据"""
        try:
            json_str = json.dumps(data, ensure_ascii=False)
        except TypeError:
            json_str = data
        try:
            with open(self.data_dir / folder / file_name, "w", encoding="utf-8") as f:
                f.write(str(json_str))
            logger.success("Data saved to " + str(self.data_dir / folder / file_name))
        except Exception as e:
            logger.error(
                "Save data " + str(self.data_dir / folder / file_name) + " failed."
            )
            logger.exception(e)

    async def spider(self, mid: int) -> None:
        """爬取单用户"""
        logger.add(f"log/log_{mid}.log")
        logger.info("Start spidering user " + str(mid))
        try:
            user_info = await self.get_user_info(mid)
        except Exception as e:
            logger.error(f"User {mid} not found.")
            logger.exception(e)
            return
        if not user_info:
            logger.error(f"User {mid} not found.")
            return
        await self.save_data(user_info, "users", str(mid) + ".json")
        try:
            video_list = await self.get_user_video_list(mid)
        except Exception as e:
            logger.error(f"Get video list of user {mid} failed.")
            logger.exception(e)
            return
        if not video_list:
            logger.error(f"User {mid} has no video.")
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            await self.save_data(
                {"time": time_str, "info": "no video"},
                "users",
                str(mid) + "_finish.json",
            )
            return
        await self.save_data(video_list, "videos", str(mid) + ".json")
        logger.info("Total " + str(len(video_list)) + " videos.")
        logger.info("Start spidering videos")
        if (
            self.config["video_limit"] != 0
            and len(video_list) > self.config["video_limit"]
        ):
            video_list = video_list[: self.config["video_limit"]]
        for video_item in video_list:
            logger.info(
                "Current progress: "
                + str(video_list.index(video_item))
                + "/"
                + str(len(video_list))
            )
            aid = video_item["aid"]
            try:
                comment_list = await self.get_video_comment_list(aid)
            except Exception as e:
                logger.error(f"Get comment list of video {aid} failed.")
                logger.exception(e)
                continue
            await self.save_data(comment_list, "comments", str(aid) + ".json")
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        await self.save_data(
            {"time": time_str, "info": "complete"},
            "users",
            str(mid) + "_finish.json",
        )
        logger.success("Spidering user " + str(mid) + " finished.")
        logger.remove()

    async def spider_all(self) -> None:
        """爬取用户列表"""
        logger.info("Start spidering all users")
        account_list = self.config["account_list"]
        for account in account_list:
            if not self.config["proxy"]:
                await sleep(randint(1, 3))
            await self.spider(account)
        logger.success("Spidering all users finished.")
