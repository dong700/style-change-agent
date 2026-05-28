# Railway 部署健康检查失败修复

## 问题诊断

Railway 显示"健康检查失败"，可能的原因：

### 1. 配置文件路径问题 ❌
**问题**：`model_config.json` 文件路径可能不正确
**错误**：`os.path.dirname(__file__)` 在某些情况下可能返回空字符串

### 2. 文件不存在 ❌
**问题**：`model_config.json` 可能没有被 Git 跟踪或上传
**错误**：`FileNotFoundError: [Errno 2] No such file or directory`

### 3. 启动失败 ❌
**问题**：代码中有语法错误或依赖缺失
**错误**：Python 启动时抛出异常

### 4. 端口配置 ❌
**问题**：没有正确监听 PORT 环境变量
**错误**：监听错误端口导致健康检查失败

## 已修复的问题

### ✅ 修复 1: 配置文件路径

**修改前**：
```python
MODEL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'model_config.json')
```

**修改后**：
```python
MODEL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_config.json')
```

使用 `os.path.abspath(__file__)` 确保获取完整的绝对路径。

### ✅ 修复 2: 自动创建默认配置

添加了配置文件不存在时的自动创建逻辑：

```python
def load_model_config():
    """加载模型配置"""
    try:
        if not os.path.exists(MODEL_CONFIG_PATH):
            # 如果配置文件不存在，创建默认配置
            default_config = {
                'current_model': 'qwen-max',
                'available_models': [
                    {'id': 'qwen-max', 'name': 'Qwen-Max'},
                    {'id': 'qwen-plus', 'name': 'Qwen-Plus'},
                    {'id': 'qwen-turbo', 'name': 'Qwen-Turbo'}
                ]
            }
            os.makedirs(os.path.dirname(MODEL_CONFIG_PATH), exist_ok=True)
            with open(MODEL_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
        
        with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载模型配置失败：{e}")
        return {
            'current_model': 'qwen-max',
            'available_models': [...]
        }
```

### ✅ 修复 3: 增强的错误处理

- 添加详细的异常捕获
- 打印错误日志到控制台
- 返回默认配置而不是崩溃

## 部署步骤

### 1. 提交并推送修复

```bash
cd c:\Users\aodon\Desktop\style_change_agent
git add .
git commit -m "修复 Railway 部署：增强配置文件错误处理"
git push
```

### 2. 等待 Railway 自动部署

Railway 会：
1. 检测到 GitHub 推送
2. 自动构建（约 1-2 分钟）
3. 自动启动应用
4. 执行健康检查

### 3. 查看部署日志

在 Railway Dashboard 中：
1. 点击你的项目
2. 查看 **Deployments** 标签
3. 点击最新的部署
4. 查看实时日志

**关键日志**：
```
✓ Build completed successfully
✓ Starting application
✓ Listening on 0.0.0.0:5000
✓ Health check passed
```

## 验证健康检查

### 健康检查端点

访问：`https://your-app.railway.app/health`

**预期响应**：
```json
{
  "status": "healthy",
  "service": "style-change-agent"
}
```

状态码应该是 `200`。

### 如果仍然失败

#### 检查点 1: 查看错误日志

在 Railway Dashboard 查看日志，寻找：
- `Error: ...`
- `Exception: ...`
- `FileNotFoundError: ...`

#### 检查点 2: 验证环境变量

确保已设置：
- `DASHSCOPE_API_KEY`（必需）
- `PORT`（通常自动设置）

#### 检查点 3: 手动测试

在 Railway 的 **Settings** → **Variables** 中临时添加：
```
DEBUG=true
```

然后在代码中添加更多日志输出。

## 常见问题

### Q1: "FileNotFoundError: model_config.json"

**原因**：文件没有被 Git 跟踪

**解决**：
```bash
# 检查文件是否被忽略
git check-ignore web_app/model_config.json

# 如果没有被忽略，强制添加
git add -f web_app/model_config.json
git commit -m "添加模型配置文件"
git push
```

### Q2: "Address already in use"

**原因**：端口被占用

**解决**：确保使用环境变量 PORT：
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

### Q3: "ModuleNotFoundError: No module named 'xxx'"

**原因**：依赖缺失

**解决**：
```bash
# 更新 requirements.txt
pip freeze > requirements.txt

# 推送
git add requirements.txt
git commit -m "更新依赖"
git push
```

### Q4: 健康检查超时

**原因**：应用启动太慢

**解决**：在 `railway.toml` 中增加超时时间：
```toml
[deploy]
healthcheckTimeout = 300  # 增加到 300 秒
```

## 完整的服务端代码检查清单

部署前检查：

- [ ] `app.py` 语法正确
- [ ] `model_config.json` 存在且格式正确
- [ ] `requirements.txt` 包含所有依赖
- [ ] `railway.toml` 配置正确
- [ ] 健康检查端点 `/health` 存在
- [ ] 使用 `PORT` 环境变量
- [ ] 监听 `0.0.0.0` 而不是 `localhost`
- [ ] `debug=False`（生产环境）

## 依赖检查

确保 `web_app/requirements.txt` 包含：

```txt
python-docx>=1.2.0
jieba>=0.42.1
langchain-community>=0.4.1
dashscope>=1.14.0
Flask>=3.0.0
Werkzeug>=3.0.0
```

## railway.toml 检查

确保配置正确：

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd web_app && python app.py"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
```

## 成功部署的标志

✅ **Build 阶段**：
```
✓ Nixpacks build started
✓ Installing dependencies
✓ Build completed successfully
```

✅ **Deploy 阶段**：
```
✓ Starting application
✓ Application started on port 5000
✓ Health check passed
✓ Deployment successful
```

✅ **服务状态**：
- Railway Dashboard 显示绿色圆点
- 状态：在线
- 健康检查：通过

## 下一步

部署成功后：

1. ✅ 访问应用 URL
2. ✅ 测试文件上传功能
3. ✅ 测试模型切换功能
4. ✅ 测试风格标签展示
5. ✅ 测试文章改写功能
6. ✅ 测试 Word 导出功能

## 总结

本次修复主要解决了：
- ✅ 配置文件路径问题（使用绝对路径）
- ✅ 文件不存在的自动处理（自动创建默认配置）
- ✅ 增强的错误处理和日志输出
- ✅ 更友好的错误提示

推送代码后，Railway 会自动重新部署。如果还有问题，请查看 Railway 的实时日志来诊断具体原因。
