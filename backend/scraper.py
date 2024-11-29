import asyncio
import json
import re
import time
from urllib.parse import parse_qs, urlparse

import jieba
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class BrowserPagePool:
    """
    单例
    浏览器页面池，用于复用浏览器实例
    避免每次都重启浏览器
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    async def start(self):
        # 使用一个浏览器单例，避免每次都重新启动浏览器
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()

    async def add_cookies(self, cookies):
        for cookie in cookies:
            if "sameSite" in cookie:
                cookie["sameSite"] = "None"
        await self.context.add_cookies(cookies)

    async def close(self):
        await asyncio.sleep(5)
        # Close the browser
        await self.browser.close()
        await self.playwright.stop()

    async def borrow_page(self):
        # 新增一个 page 用于抓取页面
        start_time = time.time()
        page = await self.context.new_page()
        print(f"Time taken: {time.time() - start_time} seconds")

        start_time = time.time()

        # 禁用图片加载
        async def block_images(route, request):
            if request.resource_type == "image":
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_images)
        print(f"Time taken: {time.time() - start_time} seconds")
        return page

    def return_page(self, page):
        # 创建关闭任务后返回，不阻塞
        asyncio.create_task(page.close())


# 全局单例
# 只在第一次使用浏览器时初始化
browser_page_pool = BrowserPagePool()

# Example cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)


async def get_html(url):
    """
    根据 url 抓取一个页面 加载后的 html 内容
    """
    # 借一个页面抓取数据
    page = await browser_page_pool.borrow_page()

    await page.goto(url)

    await page.wait_for_load_state("load")
    html_content = await page.content()

    # 归还回页面
    browser_page_pool.return_page(page)
    return html_content


async def get_search_pages_taobao(url):
    """
    抓取淘宝商品列表页，返回一个生成器，每次生成一个页面的 html 内容
    """

    # 定义常量
    NEXT_BUTTON_CLASS = (
        "button.next-btn.next-medium.next-btn-normal.next-pagination-item.next-next"
    )
    PAGES_COUNT = 5

    # 借一个页面抓取数据
    page = await browser_page_pool.borrow_page()

    await page.goto(url)

    for i in range(PAGES_COUNT):
        await page.wait_for_load_state("load")
        html_content = await page.content()
        yield html_content

        # 点击下一页
        next_button = await page.query_selector(NEXT_BUTTON_CLASS)
        if not next_button:
            break
        await next_button.click()

    # 归还回页面
    browser_page_pool.return_page(page)


def parse_search_page_taobao(html_content):
    """
    解析淘宝商品列表页，返回一个列表，每个元素是一个字典

    能在商品列表页找到的信息有：
    1. 商品名称
    2. 商品价格
    3. 商品详情页链接 / 唯一 ID
    4. 商品卡片图片链接（这个只有加载好的元素有）

    只返回 ID 列表，其余信息通过详情页抓取
    """
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    result = []
    for item in soup.find_all("a", class_=re.compile("wrapper--*")):
        url = item["href"]
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        # print("Query Params:", query_params)
        result.append(query_params["id"])
    return result


async def search_in_taobao(sentence: str):
    """
    export function
    根据搜索词搜索淘宝商品，
    使用jieba分词，
    返回一个 generator，生成元素是 商品 ID 的列表
    """
    # 使用 jieba 分词
    keyword = " ".join(jieba.lcut(sentence))
    print(f"Searching for: {keyword}")

    # 构造搜索链接
    url = f"https://s.taobao.com/search?q={keyword}"

    async for html_content in get_search_pages_taobao(url):
        result = parse_search_page_taobao(html_content)
        print(f"Got {len(result)} results from page")
        yield result


async def main():
    await browser_page_pool.start()
    await browser_page_pool.add_cookies(cookies)

    async for result in search_in_taobao("手机"):
        print(result)

    await browser_page_pool.close()


asyncio.run(main())
