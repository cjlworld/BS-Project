import asyncio
from datetime import datetime

from fastapi import FastAPI, Request, Security, Response, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessCookie
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Annotated
from sqlalchemy import select
from passlib.context import CryptContext
from contextlib import asynccontextmanager

import scraper
from models import User, Good, GoodHistory, Base 
from utils import store_multi_scraped_data, store_single_scraped_data, post_url_to_post_id, ScrapedData

from database import AsyncSessionLocal, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 创建所有表
        
    # 启动时初始化浏览器池
    await scraper.init()
    
    yield
    # 关闭时清理资源（如果有需要）
    await scraper.browser_page_pool.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 JWT 认证
access_security = JwtAccessCookie(
    secret_key="secret_key", 
    auto_error=True
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

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
    return make_response(1, "Pydantic validation error", exc.errors())

# 处理 JWT 认证错误
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: Exception):
    return make_response(1, "HTTPException", str(exc))

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
def refresh(response: Response, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    new_access_token = access_security.create_access_token(subject={"user_id": user_id})
    # Set the JWT cookies in the response
    access_security.set_access_cookie(response, new_access_token)
    return make_success_response()

@app.post('/api/user/logout')
def logout(response: Response):
    """
    用户登出
    """
    access_security.unset_jwt_cookies(response)
    return make_success_response()

@app.post('/protected')
def protected(credentials: JwtAuthorizationCredentials = Security(access_security)):
    """
    We do not need to make any changes to our protected endpoints. They
    will all still function the exact same as they do when sending the
    JWT in via a headers instead of a cookies
    """
    user_id = credentials["user_id"]
    
    return make_success_response({"user_id": user_id})


@app.post('/api/good/search')
async def search(search_req: Annotated[GoodSearchRequest, Body()]):
    keyword = search_req.keyword
    
    results = []
    async for result in scraper.search_in_smzdm(keyword):
        asyncio.create_task(store_multi_scraped_data(result))
        results.extend(result)
        
    return make_success_response({"goods": results})