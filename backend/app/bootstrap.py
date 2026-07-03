"""数据库连接的引导配置：持久化到 data/db_config.json，并提供连接测试与 URL 构建。

说明：因为"数据库连接信息"本身就是要配置的对象，无法存进数据库，所以保存为
磁盘上的 JSON 文件（通过 Docker 卷持久化），类似 WordPress 的 wp-config。
"""
import json
import os
import re
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

CONFIG_PATH = os.path.join("data", "db_config.json")
_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_$-]{1,64}$")


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
    database = _validate_database_name(cfg["database"])
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{database}?charset=utf8mb4"


def build_server_url(cfg: dict) -> str:
    """构造不指定数据库名的 MySQL 服务器连接 URL，用于首次自动建库。"""
    user = quote_plus(str(cfg["user"]))
    pw = quote_plus(str(cfg.get("password", "")))
    host = cfg["host"]
    port = int(cfg.get("port", 3306))
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/?charset=utf8mb4"


def _validate_database_name(name: str) -> str:
    """限制数据库名，避免把用户输入直接拼进 CREATE DATABASE 语句。"""
    name = str(name or "").strip()
    if not _DB_NAME_RE.fullmatch(name):
        raise ValueError("数据库名只能包含字母、数字、下划线、横线或 $，长度 1-64")
    return name


def ensure_database(cfg: dict) -> tuple[bool, str]:
    """确保目标数据库存在；不存在则自动创建。返回 (是否新建, 信息)。"""
    database = _validate_database_name(cfg["database"])
    eng = create_engine(build_server_url(cfg), connect_args={"connect_timeout": 8})
    try:
        with eng.begin() as conn:
            exists = conn.execute(
                text(
                    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                    "WHERE SCHEMA_NAME = :name"
                ),
                {"name": database},
            ).scalar()
            if exists:
                return False, f"数据库 {database} 已存在"
            conn.execute(
                text(
                    f"CREATE DATABASE `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            return True, f"数据库 {database} 已自动创建"
    finally:
        eng.dispose()


def test_connection(cfg: dict) -> tuple[bool, str]:
    """尝试连接 MySQL 服务器，返回 (是否成功, 信息)。

    注意：测试阶段不修改服务器；真正保存初始化时会自动创建目标数据库。
    """
    try:
        database = _validate_database_name(cfg["database"])
        url = build_server_url(cfg)
    except (KeyError, ValueError) as e:
        return False, f"{e}"
    eng = create_engine(url, connect_args={"connect_timeout": 8})
    try:
        with eng.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            exists = conn.execute(
                text(
                    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                    "WHERE SCHEMA_NAME = :name"
                ),
                {"name": database},
            ).scalar()
        if exists:
            suffix = f"目标数据库 {database} 已存在，将直接初始化"
        else:
            suffix = f"目标数据库 {database} 不存在，保存时会自动创建"
        return True, f"连接成功，MySQL 版本：{version}；{suffix}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        eng.dispose()
