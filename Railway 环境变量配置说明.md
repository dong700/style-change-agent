# Railway 部署配置说明

## 问题诊断

您提到"一上传就马上返回结果但是没有用 LLM 分析"，这通常是因为 **Railway 上没有设置 DASHSCOPE_API_KEY 环境变量**。

## 解决方案

### 1. 在 Railway 上设置 API Key

1. 登录 [Railway Dashboard](https://railway.app/)
2. 选择你的项目
3. 点击 **Variables** 标签页
4. 点击 **New Variable**
5. 添加以下环境变量：
   - **Key**: `DASHSCOPE_API_KEY`
   - **Value**: `sk-d313868fee5b435ebf0a7aab4f5548ed`（你的通义千问 API Key）
6. 点击 **Save**

### 2. 重新部署

保存环境变量后，Railway 会自动重新部署你的应用（约 2-3 分钟）。

### 3. 验证 LLM 分析是否工作

重新部署后，上传一个 Word 文档，检查：
- ✅ 整体风格概述应该有内容（不是"暂无整体风格概述"）
- ✅ 风格标签应该有 15-20 个标签
- ✅ 改写建议应该有 5 条左右的建议

如果 LLM 分析失败，页面上会显示红色错误信息。

## 本次修改内容

### 1. style_extractor.py

增强了 LLM 调用时的错误处理：

```python
# 检查 API Key 是否设置
api_key = os.environ.get('DASHSCOPE_API_KEY')
if not api_key:
    raise Exception("未设置 DASHSCOPE_API_KEY 环境变量，请检查 Railway 环境变量配置")

# 检查 LLM 分析是否成功
if 'error' in llm_result:
    raise Exception(f"LLM 分析失败：{llm_result.get('error', '未知错误')}")
```

### 2. templates/index.html

前端增加了错误信息显示：

```javascript
// 检查 LLM 分析是否失败
if (llmAnalysis && llmAnalysis.error) {
    // 显示红色错误信息
    document.getElementById('overallSummary').textContent = `LLM 分析失败：${llmAnalysis.error}`;
    document.getElementById('overallSummary').style.color = '#dc3545';
}
```

## 完整的 Railway 环境变量配置

你的 Railway 项目需要以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DASHSCOPE_API_KEY` | `sk-d313868fee5b435ebf0a7aab4f5548ed` | 通义千问 API Key |
| `PORT` | `5000`（通常自动设置） | Web 服务端口 |

## 本地测试

如果你想在本地测试，需要先设置环境变量：

### Windows PowerShell:
```powershell
$env:DASHSCOPE_API_KEY="sk-d313868fee5b435ebf0a7aab4f5548ed"
cd c:\Users\aodon\Desktop\style_change_agent\web_app
python app.py
```

### Linux/Mac:
```bash
export DASHSCOPE_API_KEY="sk-d313868fee5b435ebf0a7aab4f5548ed"
cd style_change_agent/web_app
python app.py
```

## 常见错误及解决方案

### 错误 1: "未设置 DASHSCOPE_API_KEY 环境变量"
**原因**: Railway 上没有设置 API Key  
**解决**: 按照上述步骤在 Railway Variables 中添加

### 错误 2: "LLM 库未安装：langchain-community 未安装"
**原因**: Railway 没有正确安装依赖  
**解决**: 检查 `requirements.txt` 是否包含 `langchain-community>=0.4.1`

### 错误 3: "JSON 解析失败"
**原因**: LLM 返回的格式不是有效的 JSON  
**解决**: 这是偶发问题，重新上传文件再试一次

### 错误 4: NLTK 相关错误
**原因**: NLTK 资源未下载  
**解决**: 已移除 NLTK 依赖，请确保已推送最新代码到 GitHub

## 提交并推送更改

记得将本次修改推送到 GitHub：

```bash
cd c:\Users\aodon\Desktop\style_change_agent
git add .
git commit -m "增强 LLM 错误处理，前端显示详细错误信息"
git push
```

Railway 会自动检测 GitHub 推送并重新部署。

## 验证清单

部署完成后，请检查：

- [ ] Railway Variables 中已设置 `DASHSCOPE_API_KEY`
- [ ] 代码已推送到 GitHub
- [ ] Railway 部署成功（绿色对勾）
- [ ] 上传 Word 文档后能看到 LLM 风格分析结果
- [ ] 风格标签数量在 15-20 个之间
- [ ] 整体风格概述有详细内容（150-250 字）

如果仍有问题，请查看 Railway 的 **Deployments** 标签页中的日志，查找 `LLM` 相关的错误信息。
