import asyncio
import json
import re
import time
from datetime import datetime
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
        
        # 设置浏览器上下文参数，模拟真实浏览器
        context_params = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "viewport": {"width": 1240, "height": 780},
            "locale": "zh-CN",
            "geolocation": {"latitude": 39.9042, "longitude": 116.4074},  # 北京的地理位置
            "permissions": ["geolocation"],
            "timezone_id": "Asia/Shanghai",
            "accept_downloads": False,
            "ignore_https_errors": False,
            "bypass_csp": False,
            "extra_http_headers": {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        }
        self.context = await self.browser.new_context(**context_params)

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
        
        # 0. 伪装, 禁用 Webdriver 标记
        await page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        """)
        print(f"Time taken: {time.time() - start_time} seconds")

        start_time = time.time()
        
        # 1. 设置 window.navigator.chrome
        # await page.evaluate("""
        #     window.navigator.chrome = {
        #         runtime: {},
        #         // etc.
        #     };
        # """)

        # 2. 绕过 navigator.permissions.query 检测
        # await page.evaluate("""
        #     const originalQuery = window.navigator.permissions.query;
        #     window.navigator.permissions.query = (parameters) => (
        #         (parameters != null && parameters.name === 'notifications') ?
        #             Promise.resolve({ state: Notification.permission }) :
        #             originalQuery(parameters)
        #     );
        # """)

        # 3. 绕过 navigator.plugins.length 检测
        await page.evaluate("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)

        # 4. 绕过 navigator.languages 检测
        await page.evaluate("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

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

    await page.wait_for_load_state('load')
    html_content = await page.content()

    # 归还回页面
    browser_page_pool.return_page(page)
    return html_content


# 定义格式化字符串
formats = [
    "%H:%M",         # 13:25
    "%m-%d %H:%M",   # 11-29 16:42
    "%Y-%m-%d"       # 2023-11-29
]

# 将时间字符串转换为 datetime 对象，没有的部分用当前时间补全
def parse_time(time_str, formats, now):
    for fmt in formats:
        try:
            # 尝试解析时间字符串
            dt = datetime.strptime(time_str, fmt)
            # 如果解析成功，补全缺失的部分
            if "%Y" not in fmt:
                dt = dt.replace(year=now.year)
            if "%m" not in fmt or "%d" not in fmt:
                dt = dt.replace(month=now.month, day=now.day)
            return dt
        except ValueError:
            continue
    raise ValueError(f"无法解析时间字符串: {time_str}")

def parse_search_page_smzdm(html_content: str):
    """
    ### SMZDM 能爬到的信息
    - 商品名: name
    - 图片地址: img 
    - 商品链接: good_url
    - POST 链接: post_url
    - 价格: price
    - 平台: platform
    - 时间（天）: time
    """
    soup = BeautifulSoup(html_content, "html.parser")
    result = []
    for item in soup.find_all("div", class_="feed-block z-hor-feed"):
        good_btn = item.find("div", class_="feed-link-btn-inner")
        if good_btn is None:
            continue
        
        good_btna = good_btn.find("a")
        if good_btna is None:
            continue
        
        img = item.find("img")
        if img is None:
            continue
        
        post_btn = item.find("a", attrs={"target": "_blank", "title": True})
        if post_btn is None:
            continue
        
        price_tag = item.find("div", class_="z-highlight")
        if price_tag is None:
            continue
        
        extra_tag = item.find("span", class_="feed-block-extras")
        if extra_tag is None:
            continue
            
        platform_tag = extra_tag.find("span")
        if platform_tag is None:
            continue
        
        data = {}
        data['img'] = img['src']
        data['name'] = img['alt']
        data['good_url'] = good_btna['href']
        data['post_url'] = post_btn['href']
        data['price'] = price_tag.text.strip()
        time_str = extra_tag.contents[0].strip()
        data['time'] = parse_time(time_str, formats, datetime.now())
        data['platform'] = platform_tag.text.strip()
        
        result.append(data)
        
    return result
    
async def search_in_smzdm(sentence: str, page_num=5):
    # 使用 jieba 分词
    keyword = "".join(jieba.lcut(sentence))
    print(f"Searching for: {keyword}")
    
    url = f"https://search.smzdm.com/?c=home&s={keyword}&v=b"
    
    for i in range(1, page_num + 1):
        html_content = await get_html(f"{url}&p={i}")
        result = parse_search_page_smzdm(html_content)
        print(f"Got {len(result)} results from page")
        yield result
    
async def main():
    await browser_page_pool.start()
    await browser_page_pool.add_cookies(cookies)

    async for result in search_in_smzdm('111 111'):
        print(result)
        pass
    
    # response = requests.get(r'https://search.smzdm.com/?c=home&s=111&v=b')
    # with open("req.html", "w", encoding='utf-8') as f:
    #     f.write(response.text)
        
    await browser_page_pool.close()

asyncio.run(main())

# 下面的弃用了

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
        try:
            # 等待，直到下一个 button 出现
            # 使用 wait_fot_load_state 会出现问题
            await page.wait_for_selector(NEXT_BUTTON_CLASS, timeout=5000)
            # await page.wait_for_load_state('load')
            
            # 点击下一页
            next_button = await page.query_selector(NEXT_BUTTON_CLASS)
            if not next_button:
                print('No next button found')
                break
            
            # 将鼠标放在 next_button 上
            await next_button.hover()
            
            html_content = await page.content()
            yield html_content
            
            await next_button.click()
        except Exception as e:
            print(f"Error occurred: {e}")
            break

    # 归还回页面
    browser_page_pool.return_page(page)
    
def parse_search_page_taobao(html_content: str):
    """
    解析淘宝商品列表页，返回一个列表，每个元素是一个字典

    能在商品列表页找到的信息有：
    1. 商品名称
    2. 商品价格
    3. 商品详情页链接 
    4. 唯一 ID（在详情页链接中有体现，不过为了方便查询，单独存一个字段）
    5. 商品卡片图片链接（这个只有加载好的元素有）

    只返回 ID 列表，其余信息通过详情页抓取
    """
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    
    with open("test.html", "w", encoding='utf-8') as f:
        f.write(html_content)
    print(f'len(html_content) = {len(html_content)}')

    result = []
    for item in soup.find_all("a", class_=re.compile("wrapper--*")):
        url = item["href"]
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        # print("Query Params:", query_params)
        result.append(query_params["id"])
    
    for item in soup.find_all("a", class_=re.compile("doubleCardWrapper*")):
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

async def parse_search_page_jd(html_content: str):
    """
    京东可以很轻易得获取到
    1. 商品名称
    2. 商品价格
    3. 商品详情页链接
    4. 唯一 ID
    5. 商品卡片图片链接
    因此返回一个字典列表，每个字典包含一个商品的这些信息
    """
    with open("test.html", "w", encoding='utf-8') as f:
        f.write(html_content)
    
    soup = BeautifulSoup(html_content, "html.parser")
    for item in soup.find_all("div", class_="gl-i-wrap"):
        print(item)
        product = {}
        product['img'] = item.find("img", attrs={'data-lazy-img': True})['img']
        print(f'img = {product["img"]}')
    return []

async def search_in_jd(sentence: str):
    # 使用 jieba 分词
    keyword = " ".join(jieba.lcut(sentence))
    print(f"Searching for: {keyword}")
    
    # 并行爬取，顺序返回
    urls = [f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8&page={i}&wq={keyword}&pvid=f29bd2beb9de4f90bb2882972612540b" for i in range(1, 6)]
    tasks = [asyncio.create_task(get_html(url)) for url in urls]
    
    # 构造搜索链接 
    for task in tasks:        
        html_content = await task
        result = await parse_search_page_jd(html_content)
        
        print(f"Got {len(result)} results from page")
        yield result
        