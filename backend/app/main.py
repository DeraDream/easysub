import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import bootstrap, database, migrate
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
from app.seed import seed_all
from app.services import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 若磁盘上已有数据库配置，则尝试初始化；否则进入安装向导模式
    if bootstrap.config_exists():
        try:
            cfg = bootstrap.load_config()
            database.init_engine(bootstrap.build_url(cfg))
            database.Base.metadata.create_all(bind=database.engine)
            migrate.run_migrations(database.engine)
            db = database.SessionLocal()
            try:
                seed_all(db)
            finally:
                db.close()
            scheduler.start_scheduler()
            print("[startup] 数据库已连接，系统就绪。")
        except Exception as e:  # noqa: BLE001
            database.reset_engine()
            print(f"[startup] 数据库初始化失败，进入安装向导模式：{e}")
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
