"""数据库连接的引导配置：持久化到 data/db_config.json，并提供连接测试与 URL 构建。

说明：因为"数据库连接信息"本身就是要配置的对象，无法存进数据库，所以保存为
磁盘上的 JSON 文件（通过 Docker 卷持久化），类似 WordPress 的 wp-config。
"""
import json
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

CONFIG_PATH = os.path.join("data", "db_config.json")


def config_exists() -> bool:
    return os.path.isfile(CONFIG_PATH)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH) or ".", exist_ok=True)
    # 不保存多余字段
    keep = {k: cfg[k] for k in ("host", "port", "user", "password", "database") if k in cfg}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=2)


def delete_config() -> None:
    if config_exists():
        os.remove(CONFIG_PATH)


def build_url(cfg: dict) -> str:
    user = quote_plus(str(cfg["user"]))
    pw = quote_plus(str(cfg.get("password", "")))
    host = cfg["host"]
    port = int(cfg.get("port", 3306))
    database = cfg["database"]
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{database}?charset=utf8mb4"


def test_connection(cfg: dict) -> tuple[bool, str]:
    """尝试连接 MySQL，返回 (是否成功, 信息)。"""
    try:
        url = build_url(cfg)
    except KeyError as e:
        return False, f"缺少字段：{e}"
    eng = create_engine(url, connect_args={"connect_timeout": 8})
    try:
        with eng.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
        return True, f"连接成功，MySQL 版本：{version}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        eng.dispose()
