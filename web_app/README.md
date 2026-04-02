# 🌐 文章风格分析 Web 应用

## 📋 功能介绍

这是一个基于 Flask 的 Web 应用，允许用户：
- 📤 **上传 Word 文档**（.docx 格式）
- 🤖 **自动分析文章风格**（使用 LLM）
- 📊 **查看详细的风格参数**（句法、词汇、可读性等）
- ✏️ **在线修改风格参数**
- 💾 **保存修改后的风格配置**

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web_app
pip install -r requirements.txt
```

### 2. 配置 API 密钥

设置通义千问 API 密钥（用于 LLM 分析）：

**Windows PowerShell:**
```powershell
$env:DASHSCOPE_API_KEY="sk-xxx"
```

**Windows CMD:**
```cmd
set DASHSCOPE_API_KEY=sk-xxx
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY=sk-xxx
```

### 3. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 4. 访问应用

打开浏览器，访问：`http://localhost:5000`

---

## 📖 使用说明

### 上传文档
1. 点击"选择文件"按钮或拖拽文件到上传区域
2. 支持 .docx 格式，最大 16MB
3. 上传后自动开始分析

### 查看分析结果
分析完成后，会显示以下信息：

#### 基本信息
- 文件名
- 总词数
- 总句数
- 段落数

#### 句法特征
- 平均句长
- 句长标准差
- 平均从句数
- 标点密度

#### 词汇特征
- 词汇丰富度
- 高频词占比
- 人称代词占比
- 情态动词密度

#### 可读性特征
- Flesch-Kincaid 等级
- 被动语态比例
- 连词密度

#### 风格标签（LLM 分析）
- 3-5 个主要风格标签
- 每个标签的强度评分（1-5 分）
- 具体的改写指导建议

#### 词频统计
- 前 50 个风格词
- 每个词的出现频率

### 修改风格参数
1. 点击任意可编辑的数值（鼠标悬停时会高亮）
2. 输入新的数值
3. 点击"💾 保存修改"按钮

---

## 🏗️ 项目结构

```
style_change_agent/
├── style_extractor.py          # 核心风格提取器
├── templates/
│   └── index.html             # 前端页面
├── web_app/
│   ├── app.py                 # Flask 后端
│   └── requirements.txt       # 依赖包
├── uploads/                    # 上传的文件（自动创建）
└── outputs/                    # 分析结果（自动创建）
```

---

## 🔌 API 接口

### 1. 上传并分析文档
```
POST /api/upload
Content-Type: multipart/form-data

参数：
- file: Word 文档文件

返回：
{
  "success": true,
  "data": {
    "基本信息": {...},
    "句法特征": {...},
    "词汇特征": {...},
    "可读性特征": {...},
    "LLM 风格分析": {...},
    "词频统计": {...}
  }
}
```

### 2. 修改风格参数
```
POST /api/modify_style
Content-Type: application/json

参数：
{
  "features": {
    "句法特征": {
      "平均句长": 10.5,
      ...
    }
  }
}

返回：
{
  "success": true,
  "message": "风格参数已更新"
}
```

### 3. 列出所有文档
```
GET /api/documents

返回：
{
  "success": true,
  "documents": [
    {
      "id": "20260330_123456_文档.docx",
      "filename": "文档.docx",
      "analyzed_at": "20260330"
    }
  ]
}
```

### 4. 获取单个文档详情
```
GET /api/documents/<doc_id>

返回：完整的分析结果 JSON
```

---

## 🎨 界面特点

- **渐变紫色背景** - 现代化设计
- **拖拽上传** - 支持点击和拖拽两种方式
- **加载动画** - 友好的等待提示
- **标签页导航** - 清晰分类展示
- **卡片式布局** - 信息分组展示
- **可编辑数值** - 点击即可修改
- **响应式设计** - 适配不同屏幕

---

## ⚠️ 注意事项

1. **LLM 分析需要网络** - 调用通义千问 API 需要联网
2. **API 调用费用** - 可能产生费用，请查看官方定价
3. **分析时间** - 每个文档约需 10-20 秒
4. **文件大小限制** - 最大 16MB
5. **仅支持 .docx** - 不支持 .doc 格式

---

## 🔧 故障排除

### 问题 1：无法启动应用
```
错误：ModuleNotFoundError: No module named 'flask'
```
**解决：**
```bash
pip install -r requirements.txt
```

### 问题 2：API 密钥错误
```
错误：Invalid API key
```
**解决：** 检查环境变量 `DASHSCOPE_API_KEY` 是否正确设置

### 问题 3：上传失败
```
错误：Request Entity Too Large
```
**解决：** 文件超过 16MB 限制，请压缩文件或拆分文档

### 问题 4：分析结果不显示
**解决：**
1. 检查浏览器控制台是否有错误
2. 确认后端服务正在运行
3. 刷新页面重试

---

## 🚀 部署建议

### 本地开发
```bash
python app.py
```

### 生产环境（Gunicorn）
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker 部署
```dockerfile
FROM python:3.12

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DASHSCOPE_API_KEY=your_api_key

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 📊 后续扩展

### 已实现
- ✅ 文档上传和分析
- ✅ 风格参数展示
- ✅ 在线修改参数
- ✅ 保存修改

### 计划中
- 📥 导出分析报告（PDF/Word）
- 📈 风格对比功能
- 📝 基于风格参数改写文本
- 🗂️ 文档管理界面
- 📊 可视化图表（词云、柱状图等）
- 👤 用户账户系统

---

## 📞 技术支持

如有问题，请检查：
- Flask 文档：https://flask.palletsprojects.com/
- 通义千问文档：https://help.aliyun.com/zh/dashscope/

---

**🎉 享受文章风格分析的乐趣！**
