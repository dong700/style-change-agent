# Railway 云端部署指南

## 部署前准备

### 1. 准备 GitHub 仓库

```bash
# 初始化 Git（如果还没有）
git init

# 添加 .gitignore
echo "*.pyc
__pycache__/
.env
*.log
.DS_Store
cache/
outputs/
uploads/
*.json
!web_app/model_config.json" > .gitignore

# 提交代码
git add .
git commit -m "Initial commit"

# 推送到 GitHub（先在 GitHub 创建仓库）
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 2. 注册 Railway 账号

访问 https://railway.app 注册账号（可用 GitHub 登录）

---

## 部署步骤

### 方法一：通过 Railway 网页部署（推荐）

1. **登录 Railway**
   - 访问 https://railway.app
   - 点击 "Login with GitHub"

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

3. **等待构建**
   - Railway 会自动检测 Python 项目
   - 根据 `requirements.txt` 安装依赖
   - 根据 `railway.toml` 配置启动

4. **设置环境变量**（可选）
   - 点击项目 → Variables
   - 添加 `DEEPSEEK_API_KEY`（如果需要默认 API Key）

5. **获取访问地址**
   - 部署成功后，Railway 会提供一个域名
   - 如：`https://your-app.up.railway.app`

### 方法二：通过 Railway CLI 部署

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 部署
railway up

# 添加域名
railway domain
```

---

## 配置说明

### railway.toml

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python web_app/app.py"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 环境变量

| 变量名 | 说明 | 是否必需 |
|--------|------|----------|
| `PORT` | Railway 自动设置 | 自动 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 用户在前端填写 |

---

## 云端限制说明

### ⚠️ 不支持的功能

云端部署**不支持**以下功能（资源限制）：

1. **OCR 功能**（扫描版 PDF）
   - PaddleOCR 需要大量内存和 CPU
   - 云端免费套餐无法运行

2. **本地文件缓存**
   - 云端文件系统是临时的
   - 重启后缓存会丢失

### ✅ 支持的功能

1. ✅ 普通文档风格分析（.docx、可编辑 PDF）
2. ✅ 风格改写
3. ✅ 超大文件处理（分批分析）
4. ✅ DeepSeek API 调用
5. ✅ 快速模式（部分片段分析）

---

## 常见问题

### Q1: 部署失败 "Build failed"

检查 `requirements.txt` 是否正确：
```bash
# 本地测试
pip install -r requirements.txt
```

### Q2: 启动后 502 错误

检查启动命令是否正确：
```bash
# 本地测试
python web_app/app.py
```

### Q3: 内存不足

Railway 免费套餐有 512MB 内存限制：
- 减小 `max_fragment_length`
- 使用快速模式减少内存占用

### Q4: 如何查看日志

Railway 控制台 → 项目 → Deployments → 点击部署 → Logs

---

## 费用说明

Railway 免费套餐：
- 每月 $5 免费额度
- 500 小时运行时间
- 适合个人使用

如果超出免费额度：
- 升级 Hobby 计划（$5/月）
- 或使用其他平台（Render、Fly.io）

---

## 一键部署按钮

可以在 README.md 中添加：

```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)
```

---

## 备选方案

如果 Railway 不满足需求，可以考虑：

| 平台 | 免费额度 | 特点 |
|------|----------|------|
| Render | 750小时/月 | 更稳定，但启动慢 |
| Fly.io | 3个小应用 | 全球节点 |
| Zeabur | 有免费额度 | 国内访问快 |
| Hugging Face Spaces | 免费 | 适合 ML 应用 |

---

## 部署后测试

部署成功后，访问以下地址测试：

1. 主页：`https://your-app.up.railway.app/`
2. 健康检查：`https://your-app.up.railway.app/health`
3. 超大文件处理：`https://your-app.up.railway.app/large_text/`
