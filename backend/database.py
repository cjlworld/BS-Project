from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import config

engine = create_async_engine(
    config['database']['database_url'],
    echo=False,
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 最大溢出连接数
    pool_recycle=3600,  # 连接回收时间（秒）
)

# 定义异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
