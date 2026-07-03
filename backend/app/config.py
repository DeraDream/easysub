from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 基础（数据库可由环境变量自动初始化；未配置时进入网页安装向导）
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    tz: str = "Asia/Shanghai"

    # Telegram
    telegram_bot_token: str = ""

    # 汇率
    exchange_api_base: str = "USD"
    exchange_api_url: str = "https://open.er-api.com/v6/latest/"
    exchange_api_key: str = ""

    # 提醒
    reminder_scan_time: str = "09:00"

    # 注册审核 / 邮件（SMTP）
    require_admin_approval: bool = True       # 新用户注册需管理员审核
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True

    # 首个管理员
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_email: str = "admin@example.com"

    # 可选：Docker/Compose 自动初始化数据库。留空时仍进入网页安装向导。
    easysub_db_host: str = ""
    easysub_db_port: int = 3306
    easysub_db_user: str = ""
    easysub_db_password: str = ""
    easysub_db_name: str = "easysub"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
