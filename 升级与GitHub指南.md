# 升级与 GitHub 同步指南

本文回答两个问题：
1. **每次改完代码，如何「只升级」而不是全新部署？**（不丢数据）
2. **如何把项目同步到自己的 GitHub 仓库？**

---

## 一、增量升级（不清空数据）

### 关键认知：你的数据本来就不会被「重建镜像」清掉
- 真正的业务数据存在你**自己的外部 MySQL**里 —— 重建容器完全不影响它。
- 数据库连接配置 + 上传的图标存在 Docker 命名卷 `app_data` 里 —— 只要不执行 `down -v` 就一直保留。
- 所以你**不需要**“全新部署”，只需重建 `app` 镜像并重启容器即可。Docker 会自动复用没变化的层（依赖没改时升级很快）。

### 推荐做法：一条命令
```bash
./update.sh
```
脚本做的事：`git pull` → `docker compose up -d --build app` → 清理悬空镜像。

> Windows 上若没有 bash，可直接手动执行下面三条：

### 手动等价命令
```bash
# 1. 更新代码（git 方式见第二节；或手动覆盖最新代码）
git pull

# 2. 只重建并重启 app（保留卷与数据库）
docker compose up -d --build app

# 3. 可选：清理旧镜像释放磁盘
docker image prune -f
```

### ⚠️ 千万不要这样做（会清空配置卷）
```bash
docker compose down -v     # -v 会删除 app_data 卷 → 需要重新跑安装向导
```
普通的 `docker compose down`（不带 `-v`）是安全的。

### 本次升级特别提醒（debug5 起新增了数据库列）
后端用 `app/migrate.py` 在启动时**自动补列**（如 `subscriptions.sort`、`users.category_order`），
所以只要按上面重启 `app` 容器即可，无需手动改数据库表结构。

---

## 二、同步到 GitHub

### 1. 在 GitHub 网站新建一个空仓库
不要勾选 “Add README / .gitignore / license”（保持空仓库，避免首次推送冲突）。
拿到仓库地址，例如：`https://github.com/你的用户名/easysub.git`

### 2. 本地初始化并首次推送（在项目目录执行）
```bash
cd /d/Claude/手机保号通知      # 你的项目路径

git init
git add .
git commit -m "init: 省心订阅 EasySub"
git branch -M main
git remote add origin https://github.com/你的用户名/easysub.git
git push -u origin main
```

> `.gitignore` 已配置好，会自动**排除**：`node_modules/`、`dist/`、`frontend_dist/`、
> `data/`、`backend/data/`、`.env`、`__pycache__/` 等。
> 也就是说**密码、数据库连接、图标缓存不会被上传**，可放心推送。

### 3. 以后每次改完代码的同步
```bash
git add .
git commit -m "本次修改说明"
git push
```

### 4. 在服务器上拉取并升级
```bash
git pull
./update.sh
```

### 认证提示
- HTTPS 方式首次推送会要求登录，**密码处需填 GitHub「Personal Access Token」**（不是账号密码）。
  生成路径：GitHub → Settings → Developer settings → Personal access tokens。
- 或改用 SSH：`git remote set-url origin git@github.com:你的用户名/easysub.git`，并提前配置 SSH key。

### 私有仓库建议
本项目虽不含密钥（`.env` 已忽略），但仍建议设为 **Private**，避免暴露你的部署细节。
