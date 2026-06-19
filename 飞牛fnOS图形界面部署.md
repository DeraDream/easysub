# 在飞牛 fnOS 用「图形界面」部署（不用命令行）

本方案**不需要构建镜像**：前端已在电脑上编译好，后端用官方 Python 镜像运行，
飞牛的 Docker 图形界面只负责"拉镜像 + 跑容器"，成功率最高。

> 用到的文件：`docker-compose.gui.yml`（已为你准备好）。

---

## 步骤总览

1. （建议）在飞牛里设置 Docker 镜像加速
2. 把项目文件夹上传到 NAS
3. 在「Docker → 项目 / Compose」里新建项目并启动
4. 打开网页 → 数据库安装向导 → 填连接 → 测试 → 保存
5. 登录使用

---

## 第 1 步：设置镜像加速（强烈建议，否则拉镜像会很慢/失败）

飞牛桌面 →「**Docker**」App →「**设置 / 仓库**」→ 找到「镜像加速 / 注册表镜像」，
加入一个国内加速地址（任选其一，失效就换）：

```
https://docker.1ms.run
https://docker.m.daocloud.io
https://dockerproxy.net
```

保存后重启 Docker 服务。这样后面拉 `python:3.12-slim` 和 `mysql:8.0` 才会快。

---

## 第 2 步：上传项目到 NAS

1. 把电脑上的整个文件夹 `D:\Claude\手机保号通知` 压缩成 zip。
2. 打开飞牛「**文件**」App → 新建一个目录，建议英文名，例如 `docker/baohao`。
3. 上传 zip 并**解压**到该目录。
4. 解压后确认目录里有这些（重点）：
   - `backend/`（后端源码）
   - `frontend/dist/`（已编译的前端，**必须存在**）
   - `docker-compose.gui.yml`

> ⚠️ 如果 `frontend/dist/` 不存在，说明前端没编译。让我重新帮你 `npm run build` 后再传，
> 或在有 Node 的电脑里进 `frontend` 跑 `npm install && npm run build`。

5. **把 `docker-compose.gui.yml` 重命名为 `docker-compose.yml`**（图形界面默认找这个名字）。
   原来那个 `docker-compose.yml`（生产用，带构建）可以先改名为 `docker-compose.build.yml` 备份。

---

## 第 3 步：在图形界面创建 Compose 项目

1. 飞牛桌面 →「**Docker**」App →「**项目**」（有的版本叫「Compose」）→「**新建 / 创建项目**」。
2. 填写：
   - **项目名称**：`baohao`
   - **路径 / 文件夹**：选你上传的目录（如 `/vol1/1000/docker/baohao`），里面要有 `docker-compose.yml`
   - 如果界面是"粘贴 YAML"模式：把 `docker-compose.gui.yml` 的内容整段粘进去，
     但**仍要把项目路径指向上面的目录**（因为要挂载 `./backend`、`./frontend/dist` 等）。
3. 点「**部署 / 构建并启动**」。
4. 飞牛会先拉 `python:3.12-slim` 和 `mysql:8.0`，然后 app 容器**首次启动会自动安装依赖**
   （约 1–3 分钟）。可以在项目里点 app 容器看「**日志**」，看到
   `Uvicorn running on http://0.0.0.0:8000` 就表示后端起来了。

---

## 第 4 步：网页配置数据库

浏览器打开：

```
http://<飞牛NAS的IP>:8842
```

首次进入会出现「**数据库安装向导**」，填入**你已有的 MySQL** 连接信息：

| 字段 | 填什么 |
|------|-----|
| 主机 host | 你的 MySQL 地址。若 MySQL 也在这台 NAS 上，填 NAS 局域网 IP（如 `192.168.1.10`），不要填 `localhost`（容器内的 localhost 指向容器自身） |
| 端口 port | 你 MySQL 的端口，默认 `3306` |
| 用户 user | 你 MySQL 的账号 |
| 密码 password | 该账号的密码 |
| 数据库 database | 要使用的库名（建议先在你的 MySQL 里建一个空库给本项目用，如 `baohao`） |

点「**测试连接**」→ 成功后点「**保存并初始化**」（会在该库里自动建表、写入预置数据、创建管理员）。

> 建议给本项目单独建一个空数据库，避免和你现有业务表混在一起。
> 若测试连接失败，多半是 host 填了 `localhost`、或 MySQL 未允许该账号从容器网段远程访问（见下方 Q4）。

---

## 第 5 步：登录

向导完成后跳到登录页，用：

```
账号：admin
密码：admin123
```

（想改默认密码：在 compose 的 `ADMIN_PASSWORD` 改，但要在**第一次初始化之前**改才生效；
已经初始化过就到网页里改或重置数据。）

---

## 常见问题

**Q1：拉镜像很慢或失败**
→ 回第 1 步配置镜像加速；或换一个加速地址。

**Q2：app 容器一直重启 / 日志报 pip 安装失败**
→ 多半是网络。compose 里已设清华 pip 源；若仍失败，把 app 的环境变量
`PIP_INDEX_URL` 换成 `https://mirrors.aliyun.com/pypi/simple/` 再重新部署。

**Q3：8842 端口被占用**
→ 编辑 compose 里 `"8842:8000"` 左边数字（如 `9000:8000`），重新部署，访问就用新端口。

**Q4：向导测试连接失败**
→ 逐项检查：
   - **host 不要填 `localhost`**：容器里的 localhost 是容器自己。MySQL 在本机就填 NAS 局域网 IP。
   - **远程访问权限**：你的 MySQL 账号要允许从容器网段连入。MySQL 里执行（按需收紧网段）：
     `CREATE USER 'baohao'@'%' IDENTIFIED BY '密码'; GRANT ALL ON baohao.* TO 'baohao'@'%'; FLUSH PRIVILEGES;`
   - **端口/防火墙**：确认 MySQL 端口对局域网开放。
   - **bind-address**：MySQL 配置里 `bind-address` 不能只绑 `127.0.0.1`，需允许局域网。

**Q5：数据存哪 / 怎么重置**
→ 业务数据在**你自己的 MySQL** 里；本项目目录 `data/` 只存连接配置(`db_config.json`)和上传图标。
   想重新走安装向导：删 `data/db_config.json` 后重启 app 容器即可（你 MySQL 里的表不会动，可自行清理）。

---

## 为什么不用"从源码构建"的图形界面方式？

图形界面也能用带 `build:` 的 compose 构建，但国内构建时 npm / pip 容易卡住、耗时久、失败率高。
本方案把前端先在电脑编译好、后端用官方镜像跑，**只拉镜像不构建**，对图形界面最友好。
如果你更想用构建方式，可改用 `docker-compose.build.yml`（即原 `docker-compose.yml`），
但需要先在 `Dockerfile` 里加国内 npm/pip 镜像（见《飞牛fnOS部署指南.md》第六节）。
