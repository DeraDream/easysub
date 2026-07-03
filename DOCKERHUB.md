# EasySub · 省心订阅

Self-hosted subscription / renewal manager with **Telegram reminders** so you never let a subscription (or a SIM-keepalive plan) expire.

自托管的订阅 / 续费 / 保号管理系统，通过 **Telegram** 提醒续费，防止忘记导致过期。

- **Source / 源码**: https://github.com/suyijun8182/easysub
- **Tags**: `latest`, `v*` (per release) — multi-arch `linux/amd64` + `linux/arm64`
- **GHCR mirror**: `ghcr.io/suyijun8182/easysub:latest`

> Use the compose file for a ready-to-run stack with MySQL 8. EasySub can also auto-initialize an external MySQL server through `EASYSUB_DB_*` environment variables.
> 推荐使用 compose 文件一键启动 EasySub + MySQL 8。也可通过 `EASYSUB_DB_*` 环境变量自动初始化外部 MySQL。

## Quick start / 快速开始

```bash
curl -O https://raw.githubusercontent.com/suyijun8182/easysub/main/docker-compose.hub.yml
docker compose -f docker-compose.hub.yml up -d
```

Then open `http://<host>:8842` and log in with the admin account from the environment variables.

## docker-compose

```yaml
services:
  app:
    image: suyijun8182/easysub:latest
    container_name: easysub
    restart: unless-stopped
    environment:
      JWT_SECRET: change-me-to-a-random-secret
      TZ: Asia/Shanghai
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: admin123
      ADMIN_EMAIL: admin@example.com
      EASYSUB_DB_HOST: db
      EASYSUB_DB_PORT: 3306
      EASYSUB_DB_USER: easysub
      EASYSUB_DB_PASSWORD: please-change-this-db-password
      EASYSUB_DB_NAME: easysub
    volumes:
      - easysub_data:/app/data
    ports:
      - "8842:8000"
    depends_on:
      db:
        condition: service_healthy
  db:
    image: mysql:8.4
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: easysub
      MYSQL_USER: easysub
      MYSQL_PASSWORD: please-change-this-db-password
      MYSQL_ROOT_PASSWORD: please-change-this-root-password
    volumes:
      - easysub_mysql:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -ueasysub -pplease-change-this-db-password --silent"]
      interval: 10s
      timeout: 5s
      retries: 12
volumes:
  easysub_data:
  easysub_mysql:
```

## Environment variables / 环境变量

| Var | Description |
|-----|-------------|
| `JWT_SECRET` | **Required.** Random secret for auth tokens. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | Initial admin account created on first init. |
| `TZ` | Timezone, e.g. `Asia/Shanghai`. |
| `REMINDER_SCAN_TIME` | Daily scan time for reminders, e.g. `09:00`. |
| `TELEGRAM_BOT_TOKEN` | Optional; can also be set in the web UI. |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | Exchange-rate source (defaults provided). |

## Volumes

- `/app/data` — DB connection config (`db_config.json`) + uploaded icons. Persist this.
- `/var/lib/mysql` — MySQL data volume when using the compose stack.

## Features

Multi-user (JWT, admin/user roles) · recurring & one-time subscriptions · multi-language (中/EN/RU) · 5 themes · multi-currency with live FX · dashboard analytics · category management · Apple-style calendar · spending reports · Telegram notifications · per-user & **admin full-site** backup/restore.

## NAS install guides

Synology / QNAP / fnOS / Unraid / TrueNAS — see [各厂家NAS安装教程.md](https://github.com/suyijun8182/easysub/blob/main/%E5%90%84%E5%8E%82%E5%AE%B6NAS%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md) in the repo.

## License

MIT · Author TG [@Aiden_SU](https://t.me/Aiden_SU) · aidensu8182@gmail.com
