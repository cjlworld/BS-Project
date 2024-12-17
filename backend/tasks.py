from sqlalchemy import select, update
from loguru import logger

import scraper
from informer import send_email
from utils import (
    store_multi_scraped_data
)
from database import AsyncSessionLocal
from models import Subscription, Good, User, GoodHistory

"""
该模块负责查询降价，并发送邮件
"""

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
        

async def check_new_price_for_all_user():
    """
    Check new price for all user
    """
    logger.debug('start check new price for all user...')
    async with AsyncSessionLocal() as session:
        all_users = await session.execute(select(User.id))
        all_users = all_users.scalars().all()
