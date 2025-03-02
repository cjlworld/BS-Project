import re
import json
import asyncio
import random
import traceback
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Request, Security, Response, Body, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessCookie
from pydantic import BaseModel, EmailStr, ValidationError, StringConstraints
from typing import Annotated
from sqlalchemy import select, delete
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from openai import OpenAI
import jieba

import scraper
from models import User, Good, GoodHistory, Base, Subscription
from utils import (
    store_multi_scraped_data, 
    post_url_to_post_id, 
    extract_float,
)
from database import AsyncSessionLocal, engine
from tasks import (
    check_new_price_for_all_user,
    check_new_price_for_user
)
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 创建所有表
        
    # 启动时初始化浏览器池
    await scraper.init()
    
    # 启动定时任务
    scheduler.start()
    scheduler.add_job(
        check_new_price_for_all_user, 
        'interval', 
        seconds=60 * 60 * 24, # 一天一大轮
        next_run_time=datetime.now() + timedelta(minutes=2) # 两分钟后执行第一次
    )
    
    yield
    
    # 关闭时清理资源（如果有需要）
    await scraper.browser_page_pool.close()
    
    # 关闭定时任务
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# 配置定时任务管理器
scheduler = AsyncIOScheduler()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors']['allow_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 JWT 认证
access_security = JwtAccessCookie(
    secret_key=config['jwt']['secret_key'],
    auto_error=True
)

# 配置密码加密
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 配置 ai_client
ai_client = OpenAI(api_key=config['openai']['api_key'], base_url="https://api.deepseek.com")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class UserRegisterRequest(BaseModel):
    email: EmailStr # 验证邮箱
    username: Annotated[str, StringConstraints(min_length=6)] # 限制 6 个字符以上
    password: Annotated[str, StringConstraints(min_length=6)] # 限制 6 个字符以上
    
class GoodSearchRequest(BaseModel):
    keyword: str
    
def make_response(code: int = 0, msg: str = "", data = None): 
    return {
        "code": code,
        "msg": msg,
        "data": data
    }

def make_success_response(data = None):
    return make_response(0, "", data)

# 处理 Pydantic 验证错误
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=200,
        content=make_response(1, "Validation error", exc.errors())
    )
# 处理 JWT 认证错误
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content=make_response(exc.status_code, exc.detail)
    )

@app.post('/api/user/login')
async def login(user: Annotated[UserLoginRequest, Body()], response: Response):
    async with AsyncSessionLocal() as session:
        statement = select(User).where(User.email == user.email)
        result = await session.execute(statement)
        user_record = result.scalars().first()
        
        if not user_record or not pwd_context.verify(user.password, user_record.password_hash):
            return make_response(1, "Invalid email or password")
        
        # Create the tokens
        access_token = access_security.create_access_token(subject={"user_id": user_record.id})
        # Set the JWT cookies in the response
        access_security.set_access_cookie(response, access_token)
        return make_success_response(access_token)

@app.post('/api/user/register')
async def register(user: Annotated[UserRegisterRequest, Body()]):
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        statement = select(User).where(User.email == user.email)
        result = await session.execute(statement)
        user_record = result.scalars().first()
        if user_record:
            return make_response(1, "User already exists")
        
        # Hash the password
        password_hash = pwd_context.hash(user.password)
        
        # Create new user
        new_user = User(email=user.email, username=user.username, password_hash=password_hash)
        session.add(new_user)
        await session.commit()
    
    return make_success_response()

@app.post('/api/user/refresh')
async def refresh(response: Response, credentials: JwtAuthorizationCredentials = Security(access_security)):
    access_token = access_security.create_refresh_token(subject=credentials.subject)
    access_security.set_refresh_cookie(response, access_token)
    return make_success_response(data={})

@app.post('/api/user/logout')
def logout(response: Response):
    """
    用户登出
    """
    access_security.unset_access_cookie(response)
    return make_success_response(data={})


@app.post('/api/good/search')
async def search(search_req: Annotated[GoodSearchRequest, Body()]):
    keyword = search_req.keyword
    
    async def search_results_streamer():
        async for result in scraper.search_in_smzdm(keyword):
            asyncio.create_task(store_multi_scraped_data(result))
    
            response = []
            for good in result:
                item = good.model_dump()
                prices = extract_float(good.price)
                if len(prices) == 0:
                    continue
                item['price'] = prices[0]
                item['post_id'] = post_url_to_post_id(good.post_url)
                del item['post_url']
                item['time'] = str(good.time)
                response.append(item)
            
            logger.info(f"search results count: {len(response)}")
            yield json.dumps(response) + '\n'
        
    return StreamingResponse(search_results_streamer(), media_type="application/x-ndjson")
    
@app.post('/api/good/ai')
def handle_ai(search_req: Annotated[GoodSearchRequest, Body()]):
    
    def get_ai_response(search_term: str):
        try:
            # 调用 OpenAI API，使用流式响应
            response = ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个给出购买建议的助手"},
                    {"role": "user", "content": f"提供一些对购买 {search_term} 的建议"}
                ],
                stream=True  # 启用流式响应
            )

            # 处理流式响应
            for chunk in response:
                try:
                    yield chunk.choices[0].delta.content  # 逐条返回内容
                except Exception:  # 如果没有内容，则忽略
                    pass
        except Exception:
            logger.warning(traceback.format_exc())
    
    return StreamingResponse(get_ai_response(search_req.keyword), media_type="text/event-stream")

class GoodDetailRequest(BaseModel):
    post_id: str

@app.post('/api/good/detail') 
async def handle_good_detail(req: GoodDetailRequest):
    async with AsyncSessionLocal() as session:
        good_details = await session.execute(
            select(Good).filter(Good.post_id == req.post_id)
        )
        good = good_details.scalars().first()
        
        if good is None:
            return make_response(code=1, msg="商品不存在")
        
        logger.info(f"good detail: post_id = {good.post_id}, url = {good.url}, name = {good.name}, img = {good.img}, platform = {good.platform}")
        
        # 从 good_history 中获取最新的价格和时间
        latest_price_time = await session.execute(
            select(GoodHistory.price, GoodHistory.time)
            .filter(GoodHistory.good_id == good.id)
            .order_by(GoodHistory.time.desc())
            .limit(1)
        )
        latest_price_time = latest_price_time.first()
        if latest_price_time is None:
            return make_response(code=1, msg="No price found")
        good.price, good.time = latest_price_time
        good.time = good.time.strftime("%Y-%m-%d %H:%M:%S")
        return make_success_response(good)
    
    
class GoodHistoryRequest(BaseModel):
    post_id: str

def gen_similar_search_regexp(sentence: str) -> str:
    # 使用 jieba 和 正则表达式 实现一个简易的 sql 模糊搜索
    # 返回正则字符串
    
    def replace_non_chinese_english_numbers_with_space(text: str) -> str:
        # 匹配非中文字符、非英文字符和非数字的部分
        pattern = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9]')
        # 使用 sub 替换为空格
        text = pattern.sub(' ', text)
        
        # 匹配连续多个空格，只保留一个
        pattern = re.compile(r'\s+')
        # 使用 sub 替换为单个空格
        return pattern.sub(' ', text)

    def any_between_words(words: List[str]) -> str:
        return '(' + '.*'.join(words) + ')'

    # 手动禁用一些词
    ban_words = [' ', '百亿', '补贴', '今日', '必买', '限地区', '以旧换新', '限', '地区', '京东', '会员']
    
    words = jieba.lcut(replace_non_chinese_english_numbers_with_space(sentence))
    # 删除 words 的 禁用词
    words = list(filter(lambda x: x not in ban_words, words))

    regexp = '(?i)' # 大小写模糊
    patterns = []
    patterns.append(any_between_words(words))
    # 如果搜索比较短, 必须所有关键字都符合
    # 否则允许少一个关键字
    if len(words) >= 6:
        for word in words:
            current_words = list(filter(lambda x: x != word, words))
            patterns.append(any_between_words(current_words))
        
    # 如果 patterns 太长了，裁剪一下
    if len(patterns) > 10:
        patterns = random.sample(patterns, 10)
    
    regexp += '.*(' + '|'.join(patterns) + ').*'
    logger.info(f'regexp for {words} is: {regexp}')
    return regexp
    
@app.post('/api/good/history')
async def handle_good_history(req: GoodHistoryRequest):
    post_id = req.post_id
    async with AsyncSessionLocal() as session:
        good = await session.execute(
            select(Good).filter(Good.post_id == post_id)
        )
        good = good.scalars().first()
        if good is None:
            return make_response(code=1, msg="No good found")
        
        logger.info(f"good found: {good}")
        
        # 生成模糊搜索词
        regexp = gen_similar_search_regexp(good.name)
        # 查找与商品名字相近的历史价格
        history = await session.execute(
            select(GoodHistory, Good)
            .join(Good, GoodHistory.good_id == Good.id)
            .where(Good.name.regexp_match(regexp))
            .order_by(GoodHistory.time.asc())
        )
        history = history.all()
        
        # 如果没有找到历史价格，返回提示
        if not history:
            return make_response(code=1, msg="No history found")
        
        # 返回历史价格数据
        return make_response(data=[
            {
                "price": history.price,
                "time": history.time.strftime("%Y-%m-%d %H:%M:%S"),
                "post_id": good.post_id,
                "name": good.name
            }
            for history, good in history
        ])
        
        
class SubscriptionRequest(BaseModel):
    good_post_id: str

# 订阅商品
@app.post('/api/subscription/add')
async def add_subscription(req: SubscriptionRequest, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    
    async with AsyncSessionLocal() as session:
        subscription = Subscription(
            good_post_id=req.good_post_id,
            user_id=user_id
        )
        session.add(subscription)
        await session.commit()
        return make_success_response(data={})

# 取消订阅
@app.post('/api/subscription/cancel')
async def cancel_subscription(req: SubscriptionRequest, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.good_post_id == req.good_post_id
            )
        )
        await session.commit()
        return make_success_response(data={})

# 查看所有订阅
@app.post('/api/subscription/get')
async def get_subscription(credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    
    async with AsyncSessionLocal() as session:
        query = await session.execute(
            select(Subscription.good_post_id)
            .filter(Subscription.user_id == user_id)
        )
        
        return make_success_response(query.scalars().all())

# 查看是否订阅
@app.post('/api/subscription/check')
async def check_subscription(req: SubscriptionRequest, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    
    async with AsyncSessionLocal() as session:
        query = await session.execute(
            select(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.good_post_id == req.good_post_id
            )
        )
        query = query.scalars().first()
        
        if query is None:
            return make_success_response({"is_subscribed": False})
        else:
            return make_success_response({"is_subscribed": True})

# 查询降价并发送邮件
@app.post('/api/subscription/email')
async def handle_subscription_email(
    background_tasks: BackgroundTasks,
    credentials: JwtAuthorizationCredentials = Security(access_security)
):
    user_id = credentials['user_id']
    background_tasks.add_task(check_new_price_for_user, user_id=user_id, always_inform=True)
    return make_success_response({})