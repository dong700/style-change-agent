# 文章风格提取器 - 使用说明

## 📋 功能概述

本工具可以提取文章的**可量化风格参数**和**不可量化风格标签**：

### 可量化特征（5 大类）
1. **句法特征** - 平均句长、句长标准差、平均从句数、标点密度
2. **词汇特征** - 词汇丰富度、词性分布、高频词占比、人称代词占比、情态动词密度
3. **可读性特征** - Flesch-Kincaid 等级、被动语态比例、连词密度
4. **韵律特征** - 平均词长、音节数分布
5. **结构特征** - 段落数、段落平均句数

### 不可量化特征（LLM 分析）
- 风格标签识别（如：古风、幽默、讽刺、口语化等）
- 每个标签的强度评分（1-5 分）
- 风格证据摘要

---

## 🚀 安装步骤

### 1. 基础安装（仅可量化特征）

```bash
pip install python-docx jieba nltk textstat
```

### 2. 完整安装（包含 LLM 分析）

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥（LLM 功能必需）

使用通义千问需要设置 API 密钥：

**Windows PowerShell:**
```powershell
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

**Windows CMD:**
```cmd
set DASHSCOPE_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

> 💡 获取 API 密钥：访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)

---

## 📖 使用方法

### 方法 1：直接运行脚本

```bash
python style_extractor.py
```

脚本会自动分析 `data/example` 目录下的所有 Word 文档。

### 方法 2：在代码中调用

```python
from style_extractor import analyze_document, print_style_report

# 分析文档（不使用 LLM）
features = analyze_document(r"你的文档路径.docx", use_llm=False)
print_style_report(features)

# 分析文档（使用 LLM）
features = analyze_document(r"你的文档路径.docx", use_llm=True)
print_style_report(features)
```

### 方法 3：单独使用 LLM 分析

```python
from style_extractor import LLMStyleAnalyzer

# 创建分析器
analyzer = LLMStyleAnalyzer(model="qwen-max")

# 分析文本
text = "你的文本内容..."
result = analyzer.analyze(text)

# 查看结果
print(result['style_labels'])
```

---

## 📊 输出示例

### 可量化特征输出
```
================================================================================
文章风格分析报告
================================================================================

📄 文件：示例文档.docx
📊 总词数：2133
📝 总句数：42
📑 段落数：91

--------------------------------------------------------------------------------
🔤 句法特征
--------------------------------------------------------------------------------
  平均句长：4.45 词
  句长标准差：14.04
  平均从句数：1.13
  标点密度：0.56 /100 词

[更多特征...]
```

### LLM 分析输出
```
--------------------------------------------------------------------------------
🤖 LLM 风格分析
--------------------------------------------------------------------------------
  风格标签:
    • 简洁：★★★★☆ (4/5)
      依据：多用短句，平均句长仅 4.45 词
    • 正式：★★★☆☆ (3/5)
      依据：被动语态使用频繁，专业术语较多
    • 客观：★★★★☆ (4/5)
      依据：人称代词使用极少，叙述客观
```

---

## 🔧 高级配置

### 修改分析目录

编辑 `style_extractor.py` 中的 `main()` 函数：

```python
example_dir = r"你的目录路径"
```

### 修改 LLM 模型

```python
# 支持的模型
analyzer = LLMStyleAnalyzer(model="qwen-max")     # 通义千问 Max
analyzer = LLMStyleAnalyzer(model="qwen-plus")    # 通义千问 Plus
analyzer = LLMStyleAnalyzer(model="qwen-turbo")   # 通义千问 Turbo
```

### 调整文本长度限制

```python
# 默认最大 2000 字符
result = analyzer.analyze(text, max_length=3000)
```

---

## 📝 依赖包清单

### 核心依赖
- `python-docx` - Word 文档处理
- `jieba` - 中文分词
- `nltk` - 英文自然语言处理
- `textstat` - 可读性计算

### LLM 依赖（可选）
- `langchain-community` - LangChain 社区版

完整清单见 `requirements.txt`

---

## ⚠️ 注意事项

1. **LLM 功能需要网络连接**：调用通义千问 API 需要联网
2. **API 调用费用**：通义千问 API 可能产生费用，请查看官方定价
3. **文本长度限制**：LLM 分析默认限制 2000 字符，过长文本会被截断
4. **中文分词准确性**：jieba 分词对专业术语可能不够准确，可自定义词典
5. **词性标注**：中文暂不支持词性标注，仅英文支持

---

## 🛠️ 故障排除

### 问题 1：LLM 功能不可用
```
警告：langchain-community 未安装，LLM 分析功能将不可用
```
**解决**：运行 `pip install langchain-community`

### 问题 2：API 密钥错误
```
Error: Invalid API key
```
**解决**：检查环境变量 `DASHSCOPE_API_KEY` 是否正确设置

### 问题 3：JSON 解析失败
**解决**：可能是 LLM 返回格式不正确，尝试更换模型或减少文本长度

### 问题 4：NLTK 资源下载失败
**解决**：手动下载 NLTK 资源或检查网络连接

---

## 📧 技术支持

如有问题，请查看：
- NLTK 文档：https://www.nltk.org/
- LangChain 文档：https://python.langchain.com/
- 通义千问文档：https://help.aliyun.com/zh/dashscope/
