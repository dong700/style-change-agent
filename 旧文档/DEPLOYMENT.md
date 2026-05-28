# Railway 部署指南

## 📋 前提条件

1. 拥有 GitHub 账号
2. 拥有 Railway 账号（可以用 GitHub 登录）
3. 已安装 Git

## 🚀 部署步骤

### 第一步：上传代码到 GitHub

#### 1. 初始化 Git 仓库

在项目根目录打开终端（PowerShell 或 CMD）：

```bash
cd c:\Users\aodon\Desktop\style_change_agent
git init
```

#### 2. 添加所有文件

```bash
git add .
```

#### 3. 提交更改

```bash
git commit -m "Initial commit: 文章风格分析系统"
```

#### 4. 创建 GitHub 仓库

1. 访问 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写仓库名称（如：`style-change-agent`）
4. 选择 "Public" 或 "Private"
5. **不要** 勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

#### 5. 关联远程仓库并推送

在终端执行（替换为您的 GitHub 用户名和仓库名）：

```bash
# 关联远程仓库
git remote add origin https://github.com/YOUR_USERNAME/style-change-agent.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 第二步：部署到 Railway

#### 1. 登录 Railway

1. 访问 https://railway.app
2. 点击 "Login" → 选择 "Login with GitHub"
3. 授权 Railway 访问您的 GitHub 仓库

#### 2. 创建新项目

1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 找到您的仓库 `style-change-agent`
4. 点击 "Connect"

#### 3. 配置环境变量

在 Railway 项目页面：

1. 点击 "Variables" 标签
2. 添加以下环境变量：
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   FLASK_ENV=production
   FLASK_APP=web_app/app.py
   ```

**重要**：将 `your_api_key_here` 替换为您的通义千问 API 密钥

#### 4. 部署

Railway 会自动开始部署，约 2-5 分钟。

部署成功后，您会看到：
- ✅ 绿色的 "Deployed" 状态
- 🌐 项目访问 URL（如：`https://style-change-agent-production.up.railway.app`）

### 第三步：访问应用

点击 Railway 提供的 URL 即可访问您的应用！

## 🔧 后续更新

当您在本地修改代码后，推送到 GitHub：

```bash
git add .
git commit -m "修复了 XXX 问题"
git push
```

Railway 会自动检测到代码更新并重新部署（约 2-3 分钟）。

## ⚙️ 高级配置

### 自定义域名

1. 在 Railway 项目页面，点击 "Settings"
2. 找到 "Domains" 部分
3. 点击 "Add Custom Domain"
4. 输入您的域名
5. 按照提示配置 DNS

### 查看日志

1. 在 Railway 项目页面，点击 "Deployments"
2. 点击最新的部署
3. 点击 "View Logs" 查看部署日志

### 数据库配置（如果需要）

1. 在 Railway 项目页面，点击 "New" → "Database" → "PostgreSQL"
2. Railway 会自动创建数据库并添加连接字符串
3. 在 "Variables" 中会自动添加 `DATABASE_URL`

## 💰 Railway 定价

- **免费额度**：$5/月（足够个人项目使用）
- **付费计划**：$5/月起，按使用量计费
- **学生优惠**：使用 GitHub Student 账号可获得额外额度

## ⚠️ 注意事项

1. **API 密钥安全**：
   - ❌ 不要将 API 密钥提交到 GitHub
   - ✅ 使用 Railway 的环境变量管理

2. **文件存储**：
   - Railway 是临时文件系统
   - 重启后上传的文件会丢失
   - 建议使用云存储（如 AWS S3）保存用户上传的文件

3. **性能优化**：
   - 首次访问可能较慢（冷启动）
   - 可以升级 Railway 计划获得更好性能

## 🐛 常见问题

**Q: 部署失败怎么办？**
A: 查看 Railway 的部署日志，通常是依赖安装失败或启动命令错误

**Q: 访问速度慢？**
A: Railway 服务器在国外，国内访问可能较慢，可以考虑使用 Cloudflare CDN

**Q: 如何绑定自定义域名？**
A: 在 Railway Settings → Domains 中添加，然后配置 DNS 的 CNAME 记录

**Q: 免费额度够用吗？**
A: 对于个人项目和小流量应用，免费额度基本够用

## 📞 获取帮助

- Railway 文档：https://docs.railway.app
- Railway Discord：https://discord.gg/railway
- GitHub Issues：在您的仓库中提 issue

---

**祝您部署成功！** 🎉
