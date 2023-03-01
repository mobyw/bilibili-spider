# bilibili-spider

## 介绍

bilibili-spider 是一个爬取 bilibili 用户、视频、评论信息的爬虫。

当前支持的功能：

- 获取用户信息
- 获取用户视频列表
- 获取视频评论列表
- 结果保存为 json 文件

## 运行

### 使用 pip

```bash
git clone https://github.com/mobyw/bilibili-spider.git
cd bilibili-spider
pip install -r requirements.txt
python ./bilibili-spider/__init__.py
```

### 使用 poetry

```bash
git clone https://github.com/mobyw/bilibili-spider.git
cd bilibili-spider
poetry install
poetry run python ./bilibili-spider/__init__.py
```

## 配置

首次运行后会自动生成配置文件 `config.json`，可在其中配置爬取的内容。

| 参数 | 类型 | 说明 | 示例 | 默认值 | 是否必填 |
| --- | --- | --- | --- | --- | --- |
| `account_list` | `list` | 要爬取的用户列表 | [114514,1919810] | [] | 是 |
| `proxy` | `bool` | 是否使用代理 | `true` | `false` | 否 |
| `proxy_api` | `str` | 代理 API | `"http://api.example.com"` | `""` | 使用代理时必填 |
| `cookie` | `str` | cookie | `"SESSDATA=xxx; bili_jct=xxx"` | `""` | 否 |
| `data_dir` | `str` | 数据保存目录 | `"./data"` | `"./data"` | 否 |
| `video_limit` | `int` | 爬取视频数量限制 | `10` | `0` | 否 |
| `comment_limit` | `int` | 爬取评论数量限制 | `100` | `0` | 否 |
| `comment_reply` | `bool` | 是否爬取评论的回复 | `true` | `false` | 否 |

## 输出

爬取的数据会保存在 `data_dir` 配置的目录下，默认为 `./data`。

```bash
├── users                   # 用户信息
│   ├── 114514.json         # 用户 114514 的信息
│   └── 1919810.json        # 用户 1919810 的信息
├── videos                  # 视频信息
│   ├── 114514.json         # 用户 114514 的视频信息
│   └── 1919810.json        # 用户 1919810 的视频信息
└── comments                # 评论信息
    ├── 1145151919.json     # 视频 1145151919 的评论信息
    └── 1919810114.json     # 视频 1919810114 的评论信息
```
