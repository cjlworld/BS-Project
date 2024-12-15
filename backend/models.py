from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

# 创建 SQLAlchemy 的 Base 类
Base = declarative_base()

# 定义 User 表
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    username = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)

# 定义 Good 表
class Good(Base):
    __tablename__ = "good"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), unique=True, nullable=False)  # 第三方平台的 postid
    name = Column(String(255), nullable=False)  # 商品名
    url = Column(Text, nullable=False)  # 商品链接
    img = Column(Text, nullable=False)  # 图片链接
    platform = Column(String(255), nullable=False)  # 购物平台
    
    def __repr__(self):
        return f"Good(id={self.id}, post_id={self.post_id}, name={self.name}, url={self.url}, img={self.img}, platform={self.platform})"

# 定义 GoodHistory 表
class GoodHistory(Base):
    __tablename__ = "good_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    good_id = Column(Integer, ForeignKey("good.id"), nullable=False)
    time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)  # 价格


class Subscription(Base):
    __tablename__ = "subscription"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    good_post_id = Column(String(255), ForeignKey("good.post_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)