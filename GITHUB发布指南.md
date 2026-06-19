# GitHub 发布完全指南

本指南将帮助你在 GitHub 上发布和管理 EasySub 项目。

---

## 前置准备

### 1. GitHub 账号和仓库

1. 如果还没有 GitHub 账号，[注册账号](https://github.com/signup)
2. 登录 GitHub，点击右上角 `+` → **New repository**
3. 填写仓库信息：
   - **Repository name**: `easysub`（或你喜欢的名字）
   - **Description**: 自托管的订阅管理系统
   - **Public**（选择公开，这样其他人才能看到）
   - ✅ **Add a README file**（可选，我们已有）
   - ✅ **Add .gitignore** → 选择 **Python**
   - ✅ **Choose a license** → 选择 **MIT License**
   - 点 **Create repository**

### 2. 配置 Git

```bash
# 配置你的 Git 用户信息
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git config --global core.autocrlf true  # Windows 用户推荐
```

### 3. 生成 SSH 密钥（推荐）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱"

# 按 Enter 接受默认位置，输入密码（可为空）

# 显示公钥
cat ~/.ssh/id_ed25519.pub  # macOS/Linux
# 或
type %USERPROFILE%\.ssh\id_ed25519.pub  # Windows PowerShell
```

在 GitHub 中添加公钥：
- Settings → SSH and GPG keys → New SSH key
- 粘贴公钥内容，保存

---

## 方案 1：从本地推送到 GitHub（推荐新项目）

### 步骤

1. **在本地初始化 Git（如果还没有）**

```bash
cd /path/to/easysub
git init
git add .
git commit -m "Initial commit: EasySub v1.0.0"
```

2. **添加远程仓库**

```bash
# 使用 SSH（推荐，已配置密钥）
git remote add origin git@github.com:你的用户名/easysub.git

# 或使用 HTTPS（需要每次输入 token）
git remote add origin https://github.com/你的用户名/easysub.git
```

3. **验证远程仓库**

```bash
git remote -v
# 应该输出：
# origin  git@github.com:你的用户名/easysub.git (fetch)
# origin  git@github.com:你的用户名/easysub.git (push)
```

4. **推送到 GitHub**

```bash
# 首次推送，创建主分支
git branch -M main
git push -u origin main

# 之后只需要
git push
```

5. **验证**
   - 访问 `https://github.com/你的用户名/easysub`
   - 确认所有文件都已上传

---

## 方案 2：克隆 GitHub 仓库到本地

如果你已在 GitHub 创建了空仓库，或想在另一台机器上工作：

```bash
# 克隆仓库
git clone git@github.com:你的用户名/easysub.git
cd easysub

# 从另一个本地仓库复制文件到这里
cp -r /original/path/to/easysub/* .

# 提交并推送
git add .
git commit -m "Initial commit: EasySub v1.0.0"
git push origin main
```

---

## 创建发布版本（Release）

### 步骤

1. **确保所有更改已提交**

```bash
git status  # 应该显示 "nothing to commit"
```

2. **创建标签**

```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial release"

# 推送标签到 GitHub
git push origin v1.0.0

# 或推送所有标签
git push origin --tags
```

3. **在 GitHub 创建 Release**

   - 访问 https://github.com/你的用户名/easysub/releases
   - 点 **Draft a new release**
   - **Choose a tag**：选择 `v1.0.0`
   - **Release title**：`v1.0.0 - Initial Release`
   - **Describe this release**：填写发布说明

```markdown
# EasySub v1.0.0 - 初始发布

🎉 首个正式版本发布！

## 主要功能

✅ 多用户系统 - JWT 鉴权，支持管理员和普通用户
✅ 订阅管理 - 支持周期订阅和一次性买断
✅ 自动提醒 - 通过 Telegram 发送续费提醒
✅ 多语言 - 中文 / English / Русский
✅ 多主题 - 5 个主题可选
✅ 多货币 - 支持全球主流货币，实时汇率
✅ 报表分析 - 详细的支出统计和趋势分析
✅ Docker 部署 - 一键部署，支持各种 NAS 平台

## 安装

详见 [README.md](https://github.com/你的用户名/easysub/blob/main/README.md)

### 快速开始

\`\`\`bash
git clone https://github.com/你的用户名/easysub.git
cd easysub
cp .env.example .env
docker compose up -d --build
\`\`\`

访问 http://localhost

## 文档

- [README](https://github.com/你的用户名/easysub/blob/main/README.md)
- [安装部署文档](https://github.com/你的用户名/easysub/blob/main/安装部署文档.md)
- [技术方案](https://github.com/你的用户名/easysub/blob/main/技术方案.md)

## 已知问题

- 暂无

## 感谢

感谢所有贡献者！
```

   - ✅ **Set as the latest release**
   - **Attach binaries**（可选，可上传 tar.gz 或 zip）
   - 点 **Publish release**

---

## 管理 GitHub 仓库

### 配置仓库设置

1. **Settings → General**
   - 设置仓库描述
   - 选择主要语言（Python）

2. **Settings → Code and automation → Actions**
   - 启用 GitHub Actions（可选，用于 CI/CD）

3. **Settings → Code security → Secret scanning**
   - 启用密钥扫描，防止意外提交敏感信息

### 添加主题标签

访问 Settings → About，添加主题标签帮助人们发现你的项目：

- `subscription-management`
- `telegram-bot`
- `fastapi`
- `vue3`
- `docker`
- `self-hosted`
- `subscription-tracker`
- `reminder-system`

### 创建项目首页（GitHub Pages 可选）

1. 启用 GitHub Pages：Settings → Pages
2. 选择 Source：Deploy from a branch
3. 选择分支：main
4. 文件夹：/ (root)
5. 发布后访问 https://你的用户名.github.io/easysub

---

## 后续维护

### 定期更新

1. **本地开发和测试**

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 修改代码
# ...

# 提交更改
git add .
git commit -m "feat: add new feature"
```

2. **推送到 GitHub**

```bash
git push origin feature/new-feature
```

3. **创建 Pull Request（PR）**
   - 访问 GitHub 仓库
   - 点 **Pull requests** → **New pull request**
   - 选择你的分支 → 填写 PR 描述 → **Create pull request**
   - 等待审查（如果是个人项目，可直接合并）

4. **合并到 main**

```bash
git checkout main
git merge feature/new-feature
git push origin main
```

### 发布新版本

```bash
# 更新版本号到 CHANGELOG.md
# 编辑 backend/app/main.py 或 frontend/package.json 的版本号
# ...

# 提交版本更新
git add .
git commit -m "chore: bump version to v1.1.0"

# 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"

# 推送
git push origin main
git push origin v1.1.0

# 在 GitHub 上创建 Release（见上文）
```

### 使用 GitHub Issues 管理任务

1. **创建 Issue** - 用于报告 Bug 或建议功能
2. **标签（Labels）** - 给 Issue 打标签（bug / feature / documentation）
3. **Milestone** - 组织 Issue 到版本（v1.1.0, v1.2.0 等）
4. **项目面板** - 用看板管理开发进度

---

## GitHub Actions（CI/CD 自动化，可选）

创建 `.github/workflows/ci.yml` 自动运行测试：

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Run tests
        run: |
          pytest backend/
```

---

## 推广项目

### 1. 项目主页优化

- ✅ 完善 README.md（已完成）
- ✅ 添加主题标签（见上文）
- ✅ 添加项目徽章（可选）

### 2. 分享项目

- Reddit: r/Python, r/SelfHosted, r/Docker 等
- Product Hunt: https://www.producthunt.com
- GitHub Trending: 自动出现
- 博客文章：撰写使用教程

### 3. 建立社区

- 启用 Discussions（Settings → General）
- 响应 Issues 和 PR
- 定期发布更新

---

## 常见问题

**Q: 如何避免提交敏感信息（密钥、密码）？**
- 使用 `.env.example` 保存示例配置
- 添加 `.env` 到 `.gitignore`
- 使用 GitHub Secrets 管理 CI/CD 中的敏感信息

**Q: 如何同步本地更改到 GitHub？**
```bash
git add .
git commit -m "描述你的更改"
git push origin main
```

**Q: 误提交了文件怎么办？**
```bash
# 从历史记录中删除文件
git rm --cached filename
echo filename >> .gitignore
git commit -m "Remove sensitive file"
```

**Q: 如何回滚到之前的提交？**
```bash
git log --oneline  # 查看提交历史
git revert <commit-hash>  # 创建反向提交
# 或
git reset --hard <commit-hash>  # 强制回滚（谨慎！）
```

---

## 检查清单

发布前的最终检查：

- [ ] README.md 完整且清晰
- [ ] LICENSE 文件已添加
- [ ] CONTRIBUTING.md 已创建
- [ ] CHANGELOG.md 已更新
- [ ] .gitignore 完整
- [ ] .env.example 包含所有必要变量
- [ ] 所有敏感信息已从代码中移除
- [ ] 本地测试通过
- [ ] 代码风格一致
- [ ] 所有文件已提交
- [ ] 标签已创建
- [ ] Release 已发布

---

**祝贺！你已成功在 GitHub 上发布了 EasySub！🎉**

有问题？查看 [GitHub 官方帮助文档](https://docs.github.com)
