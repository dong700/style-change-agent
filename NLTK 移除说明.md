# 移除 NLTK 和英文支持说明

## 修改内容

已完全移除 NLTK 和英文语言支持，项目现在**仅支持中文**文本处理。

### 修改的文件：

1. **style_extractor.py**
   - 移除 `import nltk` 和 `import textstat`
   - 移除 `from nltk.tokenize import sent_tokenize, word_tokenize`
   - 移除 `from nltk.corpus import stopwords`
   - 删除 `download_nltk_resources()` 函数
   - 简化 `StyleExtractor` 类，仅保留中文处理逻辑
   - 移除所有英文停用词、人称代词、情态动词、连词
   - 修改所有特征提取方法，使用中文分句和分词

2. **requirements.txt**（根目录）
   - 移除 `nltk>=3.9.4`
   - 移除 `textstat>=0.7.13`

3. **web_app/requirements.txt**
   - 移除 `nltk>=3.9.4`
   - 移除 `textstat>=0.7.13`

## 需要手动执行的操作

由于 Git 未安装在系统 PATH 中，请手动执行以下命令提交更改：

```bash
# 打开 Git Bash 或命令行工具
cd c:\Users\aodon\Desktop\style_change_agent

# 查看所有修改的文件
git status

# 添加所有更改
git add .

# 提交更改
git commit -m "移除 NLTK 和英文支持，仅保留中文处理，修复 Railway 部署"

# 推送到 GitHub
git push
```

## 推送后的自动部署

推送到 GitHub 后，Railway 会自动检测更改并重新部署：

1. Railway 会检测到 `requirements.txt` 的更改
2. 自动安装新的依赖（不再包含 NLTK 和 textstat）
3. 自动重启应用
4. 等待 2-3 分钟部署完成

## 验证部署

部署完成后，访问你的 Railway 应用 URL，测试以下功能：

- ✅ 上传 Word 文档
- ✅ 风格分析
- ✅ 文章改写
- ✅ 导出 Word

不再会出现 "Resource 'punkt_tab' not found" 错误。

## 技术细节

### 中文处理替代方案

**英文（已移除）：**
```python
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

sentences = sent_tokenize(text)  # 英文分句
words = word_tokenize(text)      # 英文分词
stop_words = stopwords.words('english')
```

**中文（现在使用）：**
```python
import jieba
import re

sentences = re.split(r'[。！？.!?]', text)  # 中文分句
words = list(jieba.cut(text))              # 中文分词
stop_words = {'的', '了', '在', ...}       # 中文停用词
```

### 音节计数简化

**英文（已移除）：**
```python
import textstat
syllables = textstat.syllable_count(word)  # 需要字典
```

**中文（现在使用）：**
```python
# 中文每个汉字一个音节
chinese_chars = [c for c in self.text if '\u4e00' <= c <= '\u9fff']
syllable_counts = [1] * len(chinese_chars)
avg_syllables = 1.0
```

## 影响范围

### 移除的功能
- ❌ 英文文本处理
- ❌ NLTK 分词和词性标注
- ❌ textstat 可读性计算（Flesch-Kincaid 等）
- ❌ 英文停用词过滤

### 保留的功能
- ✅ 中文分词（jieba）
- ✅ 中文分句（正则表达式）
- ✅ 中文停用词过滤
- ✅ 所有可量化特征提取（句法、词汇、可读性、韵律、结构）
- ✅ LLM 风格分析
- ✅ 文章改写
- ✅ Word 导出

## 为什么选择移除英文支持？

1. **部署复杂性**：NLTK 需要在 Railway 上下载资源文件（punkt_tab），增加了部署复杂度
2. **项目定位**：项目主要面向中文文章风格改写
3. **依赖简化**：减少依赖包数量，提高部署成功率
4. **性能优化**：避免每次启动时检查/下载 NLTK 资源

如果未来需要支持英文，可以：
- 使用预构建的 Docker 镜像包含 NLTK 资源
- 或使用其他不需要下载资源的 NLP 库（如 spaCy）
