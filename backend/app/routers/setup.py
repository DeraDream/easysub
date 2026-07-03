from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import bootstrap, database
from app.initializer import initialize_database

router = APIRouter(prefix="/api/setup", tags=["setup"])


class DBConfig(BaseModel):
    host: str
    port: int = 3306
    user: str
    password: str = ""
    database: str = "easysub"


@router.get("/status")
def status():
    return {
        "configured": database.is_configured(),  # 引擎已就绪可用
        "config_present": bootstrap.config_exists(),  # 磁盘上已有配置文件
    }


@router.post("/test")
def test(cfg: DBConfig):
    ok, msg = bootstrap.test_connection(cfg.model_dump())
    if not ok:
        raise HTTPException(400, f"连接失败：{msg}")
    return {"ok": True, "message": msg}


@router.post("/save")
def save(cfg: DBConfig):
    if database.is_configured():
        raise HTTPException(400, "系统已完成数据库配置")
    ok, msg = bootstrap.test_connection(cfg.model_dump())
    if not ok:
        raise HTTPException(400, f"连接失败：{msg}")
    try:
        initialize_database(cfg.model_dump(), create_database=True)
    except Exception as e:  # noqa: BLE001
        database.reset_engine()
        raise HTTPException(500, f"初始化失败：{type(e).__name__}: {e}")
    bootstrap.save_config(cfg.model_dump())
    return {"ok": True, "message": "数据库已配置并初始化完成，请登录"}
