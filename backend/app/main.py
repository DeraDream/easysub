import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import bootstrap, database
from app.config import settings
from app.initializer import initialize_database
from app.routers import (
    admin,
    auth,
    backup,
    bundles,
    categories,
    currencies,
    dashboard,
    icons,
    logs,
    notifications,
    payment_methods,
    reports,
    setup,
    subscriptions,
    system,
    users,
)
from app.services import scheduler


def _env_db_config() -> dict | None:
    if not settings.easysub_db_host or not settings.easysub_db_user:
        return None
    return {
        "host": settings.easysub_db_host,
        "port": settings.easysub_db_port,
        "user": settings.easysub_db_user,
        "password": settings.easysub_db_password,
        "database": settings.easysub_db_name,
    }


def _initialize_with_retry(cfg: dict, *, persist_config: bool) -> None:
    last_error = None
    for attempt in range(1, 31):
        try:
            initialize_database(cfg, create_database=True, persist_config=persist_config)
            return
        except Exception as e:  # noqa: BLE001
            database.reset_engine()
            last_error = e
            if attempt < 30:
                print(f"[startup] 数据库初始化等待中（{attempt}/30）：{e}")
                time.sleep(2)
    raise last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 若磁盘上已有数据库配置，则尝试初始化；否则可从环境变量自动初始化或进入安装向导模式
    if bootstrap.config_exists():
        try:
            cfg = bootstrap.load_config()
            initialize_database(cfg, create_database=False)
            print("[startup] 数据库已连接，系统就绪。")
        except Exception as e:  # noqa: BLE001
            database.reset_engine()
            print(f"[startup] 数据库初始化失败，进入安装向导模式：{e}")
    else:
        cfg = _env_db_config()
        if cfg:
            try:
                _initialize_with_retry(cfg, persist_config=True)
                print("[startup] 已通过环境变量自动初始化数据库，系统就绪。")
            except Exception as e:  # noqa: BLE001
                database.reset_engine()
                print(f"[startup] 环境变量自动初始化失败，进入安装向导模式：{e}")
        else:
            print("[startup] 未检测到数据库配置，进入安装向导模式。")
    yield
    scheduler.shutdown_scheduler()


app = FastAPI(title="订阅保号通知系统 API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    setup.router,
    auth.router,
    users.router,
    categories.router,
    payment_methods.router,
    currencies.router,
    subscriptions.router,
    bundles.router,
    dashboard.router,
    reports.router,
    notifications.router,
    icons.router,
    admin.router,
    logs.router,
    system.router,
    backup.router,
):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "configured": database.is_configured()}


# 静态资源（上传的图标）
os.makedirs(os.path.join("data", "icons"), exist_ok=True)
app.mount("/static/icons", StaticFiles(directory=os.path.join("data", "icons")), name="icons")

# 前端构建产物（若存在则托管，实现单服务部署 + SPA history 路由兜底）
_frontend_dist = os.path.join("frontend_dist")
if os.path.isdir(_frontend_dist):
    _assets = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
