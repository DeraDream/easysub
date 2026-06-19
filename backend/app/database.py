"""数据库引擎在运行时由网页安装向导配置后初始化（不再依赖启动时的环境变量）。"""
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


# 运行时由 init_engine() 赋值；未配置前为 None
engine = None
SessionLocal = None


def init_engine(url: str):
    """根据 SQLAlchemy URL 初始化全局引擎与会话工厂。"""
    global engine, SessionLocal
    connect_args = {}
    if url.startswith("mysql"):
        connect_args = {"connect_timeout": 10}
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def is_configured() -> bool:
    return SessionLocal is not None


def reset_engine():
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    engine = None
    SessionLocal = None


def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="数据库尚未配置，请先在安装向导中配置数据库连接")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
