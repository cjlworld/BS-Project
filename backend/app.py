from fastapi import FastAPI, Request, Security, Response, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessCookie
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Annotated
from sqlmodel import SQLModel, Field, create_engine, Session, select
from passlib.context import CryptContext
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    SQLModel.metadata.create_all(engine)
    yield
    # 关闭时清理资源（如果有需要）
    # 例如：关闭数据库连接

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

# 配置数据库连接
DATABASE_URL = "mysql+pymysql://root:root@localhost:3307/bs"
engine = create_engine(DATABASE_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr
    username: str
    password_hash: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    
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
def login(user: Annotated[UserLogin, Body()], response: Response):
    with Session(engine) as session:
        statement = select(User).where(User.email == user.email)
        result = session.exec(statement).first()
        
        if not result or not pwd_context.verify(user.password, result.password_hash):
            return make_response(1, "Invalid email or password")
        
        # Create the tokens
        access_token = access_security.create_access_token(subject={"user_id": result.id})
        # Set the JWT cookies in the response
        access_security.set_access_cookie(response, access_token)
        return make_success_response(access_token)

@app.post('/api/user/register')
def register(user: Annotated[UserRegister, Body()]):
    with Session(engine) as session:
        # Check if user already exists
        statement = select(User).where(User.email == user.email)
        result = session.exec(statement).first()
        if result:
            return make_response(1, "User already exists")
        
        # Hash the password
        password_hash = pwd_context.hash(user.password)
        
        # Create new user
        new_user = User(email=user.email, username=user.username, password_hash=password_hash)
        session.add(new_user)
        session.commit()
    
    return make_success_response()

@app.post('/refresh')
def refresh(response: Response, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials["user_id"]
    new_access_token = access_security.create_access_token(subject={"user_id": user_id})
    # Set the JWT cookies in the response
    access_security.set_access_cookie(response, new_access_token)
    return make_success_response()

@app.delete('/api/user/logout')
def logout(response: Response):
    """
    用户登出
    """
    access_security.unset_jwt_cookies(response)
    return make_success_response()

@app.get('/protected')
def protected(credentials: JwtAuthorizationCredentials = Security(access_security)):
    """
    We do not need to make any changes to our protected endpoints. They
    will all still function the exact same as they do when sending the
    JWT in via a headers instead of a cookies
    """
    user_id = credentials["user_id"]
    
    return make_success_response({"user_id": user_id})