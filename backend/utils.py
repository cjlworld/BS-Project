import re
from urllib.parse import urlparse
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from loguru import logger

from models import Good, GoodHistory
from database import AsyncSessionLocal

class ScrapedData(BaseModel):
    platform: str
    post_url: str
    img: str
    name: str
    url: str
    price: str
    time: datetime

def post_url_to_post_id(url: str) -> str:
    # https://www.smzdm.com/p/135985444/
    # 目前只做了 smzdm.com 的解析，其他平台未做
    parse_result = urlparse(url)
    assert url.startswith('https://www.smzdm.com/p/')
    
    path = parse_result.path.rstrip("/")
    smzdm_id = path.split('/')[-1]
    return f'smzdm_{smzdm_id}'

def extract_float(text: str) -> list[float]:
    """
    从字符串中提取所有浮点数。

    :param text: 输入的字符串
    :return: 提取的浮点数列表
    """
    # 正则表达式匹配浮点数
    # -? 匹配可选的负号
    # \d+ 匹配一个或多个数字
    # \.? 匹配可选的小数点
    # \d* 匹配小数点后的可选数字
    pattern = r'-?\d+\.?\d*'
    
    # 查找所有匹配的浮点数
    matches = re.findall(pattern, text)
    
    # 将匹配的字符串转换为浮点数
    return [float(match) for match in matches]

async def store_single_scraped_data(data: ScrapedData):
    async with AsyncSessionLocal() as session:
        good = Good(
            post_id=post_url_to_post_id(data.post_url),
            name=data.name,
            url=data.url,
            img=data.img,
            platform=data.platform
        )
        
        # 先搜索 post_id 是否已经存在
        query = await session.execute(
            select(Good).filter(Good.post_id == good.post_id)
        )
        
        first_good = query.scalars().first()  # 获取第一个匹配的记录
        if first_good is None:
            session.add(good)
            await session.commit()
            await session.refresh(good)
        else:
            good = first_good
        
        price = extract_float(data.price)
        if len(price) == 0:
            return
        
        # 查找是否存在时间一样，商品一样的记录
        first_history = await session.execute(
            select(GoodHistory)
            .filter(GoodHistory.good_id == good.id)
            .filter(GoodHistory.time == data.time)
        )
        first_history = first_history.first()
        if first_history is not None:
            return
        
        good_history = GoodHistory(
            good_id=good.id,
            price=price[0],
            time=data.time
        )
        session.add(good_history)
        await session.commit()

async def store_multi_scraped_data(datas: list[ScrapedData]):
    logger.debug(f"store_multi_scraped_data len: {len(datas)}")
    # 顺序插入，避免爆连接池
    for data in datas:
        await store_single_scraped_data(data)
    # tasks = [store_single_scraped_data(data) for data in datas]
    # await asyncio.gather(*tasks)