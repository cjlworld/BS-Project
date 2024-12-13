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

# 创建 SQLAlchemy 的 Base 类
Base = declarative_base()

# 定义 User 表
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

# 定义 Good 表
class Good(Base):
    __tablename__ = "good"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, unique=True, nullable=False)  # 第三方平台的 postid
    name = Column(String, nullable=False)  # 商品名
    url = Column(Text, nullable=False)  # 商品链接
    img = Column(String, nullable=False)  # 图片链接
    platform = Column(String, nullable=False)  # 购物平台

# 定义 GoodHistory 表
class GoodHistory(Base):
    __tablename__ = "good_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    good_id = Column(Integer, ForeignKey("good.id"), nullable=False)
    time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)  # 价格
