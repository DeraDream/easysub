# 在飞牛 fnOS 的 Docker 里测试本项目

目标：把项目跑在飞牛 NAS 上，用浏览器访问 `http://<NAS的IP>:8842` 测试。
推荐用 **SSH + docker compose**（因为项目要从源码构建，命令行最稳）。

---

## 一、准备：开启 SSH

1. 飞牛桌面 →「设置」→「系统」→ 找到 **SSH / 终端**（或「远程访问」），打开 SSH 服务，记下端口（默认 22）。
2. 记下 NAS 的局域网 IP（设置 → 网络，例如 `192.168.1.10`）。

---

## 二、把项目传到 NAS

任选一种：

**方式 A：用飞牛「文件管理」上传（最简单）**
1. 把电脑上的整个文件夹 `D:\Claude\手机保号通知` 压缩成 zip。
2. 飞牛「文件」App 里新建目录，例如 `docker/baohao`，上传 zip 并解压。
   - ⚠️ 建议目录名用英文 `baohao`，避免中文路径在命令行里出问题。

**方式 B：用 SMB 共享拖拽**
- 在 Windows 资源管理器输入 `\\192.168.1.10`，登录后把文件夹拖进共享目录。

传完后，项目应位于类似：`/vol1/1000/docker/baohao`（具体路径在「文件」里右键→属性可看到）。

---

## 三、SSH 登录并启动

Windows 上打开 PowerShell 或 CMD：

```bash
ssh 你的用户名@192.168.1.10
# 输入密码登录

# 进入项目目录（按你的实际路径改）
cd /vol1/1000/docker/baohao

# 确认 docker 可用
docker version
docker compose version

# 构建并启动（首次会编译前端+后端，约 3-8 分钟）
docker compose -f docker-compose.fnos.yml up -d --build
```

> 如果提示当前用户没权限执行 docker，命令前加 `sudo`：
> `sudo docker compose -f docker-compose.fnos.yml up -d --build`

启动完成后访问：

```
http://192.168.1.10:8842
```

**首次访问会出现「数据库安装向导」**（因为数据库连接由你在网页上配置）。
填入**你已有的 MySQL** 连接信息：

| 字段 | 填什么 |
|------|-----|
| 主机 host | 你的 MySQL 地址；若在本机填 NAS 局域网 IP（如 `192.168.1.10`），**不要填 `localhost`** |
| 端口 port | 你 MySQL 的端口，默认 `3306` |
| 用户 user | 你 MySQL 的账号 |
| 密码 password | 该账号密码 |
| 数据库 database | 给本项目用的库名（建议先建一个空库，如 `baohao`） |

点「**测试连接**」显示成功后，再点「**保存并初始化**」。系统会在该库里自动建表、写入预置分类/货币、
创建管理员账户，然后跳转登录页。

用 `admin / admin123` 登录（可在 compose 的 `ADMIN_PASSWORD` 改）。

> 建议给本项目单独建一个空库，避免和你现有业务表混在一起。
> 测试连接失败常见原因：host 填了 `localhost`、MySQL 账号未授权从容器网段远程访问、或 `bind-address` 只绑了本地。

---

## 四、常用命令

```bash
# 看运行状态
docker compose -f docker-compose.fnos.yml ps

# 看日志（排错用，Ctrl+C 退出）
docker compose -f docker-compose.fnos.yml logs -f

# 停止
docker compose -f docker-compose.fnos.yml down

# 改了代码后重新构建
docker compose -f docker-compose.fnos.yml up -d --build
```

---

## 五、Telegram 测试

1. Telegram 找 **@BotFather** → `/newbot` 创建机器人，拿到 Token。
2. 编辑 `docker-compose.fnos.yml`，把 `TELEGRAM_BOT_TOKEN: ""` 填上 Token。
3. 重新启动：`docker compose -f docker-compose.fnos.yml up -d`
4. 网页「设置」→「验证机器人」→ 给机器人发条消息 →「获取 Chat ID」→ 保存 →「发送测试」。

---

## 六、常见问题

**1. 构建很慢 / npm 或 pip 卡住（国内网络）**
在项目根目录的 `Dockerfile` 里加国内镜像。把下面两处替换：

- 前端那一行 `RUN npm ci || npm install` 改为：
  ```dockerfile
  RUN npm config set registry https://registry.npmmirror.com && (npm ci || npm install)
  ```
- 后端那一行 `RUN pip install -r requirements.txt` 改为：
  ```dockerfile
  RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
  ```
然后重新 `up -d --build`。

**2. 8842 端口被占用**
改 `docker-compose.fnos.yml` 里 `"8842:8000"` 左边的数字，比如 `"9000:8000"`，访问就用 9000。

**3. 访问不了**
- 确认容器在跑：`docker compose -f docker-compose.fnos.yml ps`
- 看日志有没有报错：`... logs -f`
- 飞牛防火墙是否放行了该端口。

**4. 数据存在哪**
- 业务数据在**你自己的 MySQL** 里（本项目不自带数据库）。
- 本项目目录 `data/` 只存数据库连接配置(`data/db_config.json`)和上传的图标。

**5. 想重新走安装向导**
删掉 `data/db_config.json` 后重启 app 容器即可（你 MySQL 里的表不会动）。

---

## 七、想用图形界面而不是命令行？

飞牛较新版本的「Docker」App 支持「Compose / 项目」导入：
1. 打开 Docker App →「项目」→「新建」。
2. 选择项目所在目录（含 `docker-compose.fnos.yml`），或粘贴该文件内容。
3. 创建并构建。

但「从 Dockerfile 构建」在 UI 里偶有兼容问题，若失败请回到上面的 SSH 命令行方式。
```
