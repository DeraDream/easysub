# 各厂家 NAS 安装教程（EasySub 省心订阅）

> 本项目已发布到 **Docker Hub** 和 **GitHub Container Registry (GHCR)**，
> NAS 部署**不再需要从源码构建**，直接拉取镜像即可运行。

镜像地址（任选其一）：

| 来源 | 镜像名 |
|------|--------|
| Docker Hub | `suyijun8182/easysub:latest` |
| GHCR（GitHub） | `ghcr.io/suyijun8182/easysub:latest` |

> 国内拉取 Docker Hub 较慢时，建议先配置镜像加速，或改用 GHCR。

## 通用前置条件

1. NAS 已安装 **Docker / Container** 套件。
2. 推荐使用本仓库的 `docker-compose.hub.yml` 创建项目；它会同时启动 EasySub 和 MySQL 8，数据库会自动初始化。
3. 关键环境变量（创建项目/容器时填）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `JWT_SECRET` | 登录令牌密钥，**必须改成随机串** | `openssl rand -hex 32` 生成 |
| `ADMIN_USERNAME` | 初始管理员账号 | `admin` |
| `ADMIN_PASSWORD` | 初始管理员密码（首次初始化后请改） | `admin123` |
| `ADMIN_EMAIL` | 管理员邮箱 | `admin@example.com` |
| `TZ` | 时区 | `Asia/Shanghai` |
| `REMINDER_SCAN_TIME` | 每天提醒扫描时间 | `09:00` |
| `TELEGRAM_BOT_TOKEN` | 可留空，后续网页里配 | |
| `EASYSUB_DB_PASSWORD` | EasySub 连接内置 MySQL 的密码，建议改强密码 | `change-me-db-password` |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码，建议改强密码 | `change-me-root-password` |

- **端口**：容器内部 `8000`，映射到宿主任意端口（本文统一用 `8842`）。
- **持久化目录**：EasySub 的 `/app/data` 存连接配置和上传图标；MySQL 的 `/var/lib/mysql` 存业务数据，二者都要持久化。

完成创建后，浏览器访问 `http://<NAS局域网IP>:8842`，用上面的管理员账号登录即可。若未配置 `EASYSUB_DB_*` 环境变量，才会进入安装向导。

---

## 1. 群晖 Synology（DSM 7 / Container Manager）

1. 打开 **Container Manager**（旧版叫 Docker）。
2. **注册表** → 搜索 `suyijun8182/easysub` → 下载 `latest` 标签。
3. **映像** → 选中镜像 → **运行**。
4. 在向导里设置：
   - **端口设置**：本地端口 `8842` → 容器端口 `8000`。
   - **存储空间**：添加文件夹，装载路径填 `/app/data`（如 `/docker/easysub` → `/app/data`）。
   - **环境**：逐条添加上表的变量（`JWT_SECRET`、`ADMIN_*`、`TZ` 等）。
5. 启动后访问 `http://<群晖IP>:8842`。

> 也可用「项目（Project）」功能：上传本仓库的 `docker-compose.hub.yml`，新建项目直接部署。

---

## 2. 威联通 QNAP（Container Station）

1. 打开 **Container Station**。
2. **创建** → **搜索镜像** → 输入 `suyijun8182/easysub` → 选 `latest` 创建。
3. **高级设置**：
   - **网络**：端口转发 `8842 → 8000`。
   - **存储空间**：挂载一个卷到 `/app/data`。
   - **环境变量**：添加上表变量。
4. 创建并启动，访问 `http://<威联通IP>:8842`。

> Container Station 新版支持「**应用程序（Application）**」用 docker-compose：把 `docker-compose.hub.yml` 内容粘进去即可。

---

## 3. 飞牛 fnOS

1. 飞牛桌面 → **Docker** App → **设置 / 仓库** → 配置镜像加速（强烈建议）：
   ```
   https://docker.1ms.run
   https://docker.m.daocloud.io
   ```
2. **镜像** → 搜索并拉取 `suyijun8182/easysub:latest`。
3. **容器** → 用该镜像创建：
   - 端口 `8842 → 8000`；
   - 目录映射 `/app/data`；
   - 添加上表环境变量。
4. 或用 **项目 / Compose**：粘贴 `docker-compose.hub.yml` 内容创建项目（推荐，最省事）。
5. 访问 `http://<飞牛IP>:8842`。

> 旧版「图形界面从源码部署」的方式已不再需要——现在直接拉取发布镜像即可。

---

## 4. Unraid

1. **Apps / Community Applications** 里搜索，或用 **Docker → Add Container** 手动添加。
2. 手动添加时：
   - **Repository**：`suyijun8182/easysub:latest`
   - **Network Type**：Bridge
   - **Port**：`8842` → `8000`
   - **Path**：`/mnt/user/appdata/easysub` → `/app/data`
   - **Variables**：逐条加上表环境变量。
3. Apply 启动，访问 `http://<Unraid IP>:8842`。

---

## 5. TrueNAS SCALE（Custom App）

1. **Apps** → **Discover** → **Custom App**。
2. 填写：
   - **Image Repository**：`suyijun8182/easysub`，**Tag**：`latest`
   - **Container Port** `8000`，**Node Port** 选一个（如 `8842`）。
   - **Environment Variables**：加上表变量。
   - **Storage**：Host Path 或 ixVolume 挂到 `/app/data`。
3. 安装后访问 `http://<TrueNAS IP>:<NodePort>`。

---

## 6. 任意支持 Docker 的设备（命令行）

```bash
# 拉取并运行（数据库在网页向导里配置）
docker run -d --name easysub \
  -p 8842:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=admin123 \
  -e ADMIN_EMAIL=admin@example.com \
  -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

或使用仓库内 compose：

```bash
docker compose -f docker-compose.hub.yml up -d
```

---

## 升级到新版本

数据都在**你自己的 MySQL** 里，升级只换镜像，不会丢数据：

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

NAS 图形界面：在镜像里重新拉取 `latest`，再重建容器（保持 `/app/data` 映射不变）即可。

> 建议升级前，先在网页 **设置 → 数据备份** 里导出一份备份；管理员还可用 **整站备份** 导出全部成员数据。

---

## 常见问题

**Q：向导测试数据库连接失败？**
- 使用推荐 compose 部署时通常不会出现安装向导；如果出现，先确认 `db` 容器健康、`EASYSUB_DB_*` 环境变量存在且密码一致。
- host 不要填 `localhost`，要填 MySQL 的局域网 IP。
- MySQL 账号需允许从容器网段远程连接：
  `CREATE USER 'easysub'@'%' IDENTIFIED BY '密码'; GRANT ALL PRIVILEGES ON easysub.* TO 'easysub'@'%'; FLUSH PRIVILEGES;`
  这里的 `easysub` 是安装向导里填写的目标数据库名，数据库可以尚未存在，EasySub 会在初始化时创建。
- 确认 MySQL 的 `bind-address` 不是只绑 `127.0.0.1`，端口对局域网开放。

**Q：端口被占用？**
- 把映射左边的 `8842` 改成别的端口（如 `9000`），访问就用新端口。

**Q：数据存在哪 / 如何重置向导？**
- 业务数据在你自己的 MySQL；容器 `/app/data` 只存连接配置(`db_config.json`)和上传图标。
- 删掉 `/app/data/db_config.json` 重启容器，即可重新走安装向导（MySQL 里的表不动）。
