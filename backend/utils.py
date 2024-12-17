import re
import asyncio
from urllib.parse import urlparse
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import select, update

from models import Good, GoodHistory, User, Subscription
from database import AsyncSessionLocal
from informer import send_email
import scraper

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
    tasks = [store_single_scraped_data(data) for data in datas]
    await asyncio.gather(*tasks)


async def check_price_and_email(user_id: int, post_id: str, always_inform=False) -> bool:
    """
    检查价格，如果价格有变化，就发送邮件
    返回是否发送了邮件
    """
    async with AsyncSessionLocal() as session:
        # 先找到 good 对象
        good = await session.execute(
            select(Good).filter_by(post_id=post_id)
        )
        good = good.scalar()
        if good is None:
            return False

        # 找到用户的邮箱
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar()
        if user is None:
            return False
    
    async for result in scraper.search_in_smzdm(good.name, page_num=1):
        await store_multi_scraped_data(result)
    
    # 查看有没有当天的价格
    async with AsyncSessionLocal() as session:
        # 先找到订阅
        subs = await session.execute(
            select(Subscription).filter_by(good_post_id=post_id)
        )
        subs = subs.scalar()
        if subs is None:
            return False
        
        history = await session.execute(
            select(GoodHistory)
            .where(
                GoodHistory.good_id == good.id,
                GoodHistory.time > subs.last_notification_time,
            )
            .order_by(GoodHistory.time.desc())
            .limit(1)
        )
        
        history = history.scalar()
        # history 是最新的记录
        # history.price 是最新的价格
        if history is None:
            if always_inform:
                await send_email(
                    subject="启真智选：您订阅的商品价格不变",
                    body=f"商品 {good.name} 的价格没有变化，该功能仅供测试",
                    to_email=user.email,
                )
                return True
        else:
            # 更新 last_notification_time
            await session.execute(
                update(Subscription)
                .where(Subscription.id == subs.id)
                .values(last_notification_time=history.time)
            )
            send_email(
                subject="启真智选：您订阅的商品有新价格啦！",
                body=f"商品 {good.name} 的最新价格是 {history.price}，请及时关注。",
                to_email=user.email
            )
    return True

# 查看用户订阅的是否有新价格
async def check_new_price_for_user(user_id: int, always_inform=False):
    """
    检查用户订阅的所有商品是否有新的价格
    always_inform: 是否总是通知，如果为 False，则只会返回有变化的商品的列表
    会提交提交任务
    """
    async with AsyncSessionLocal() as session:
        subscriptions = await session.execute(
            select(Subscription.good_post_id)
            .filter(Subscription.user_id == user_id)
        )
        subscriptions = subscriptions.scalars().all()
    
    if subscriptions is None: 
        return
    
    for post_id in subscriptions:
        await check_price_and_email(user_id, post_id, always_inform)