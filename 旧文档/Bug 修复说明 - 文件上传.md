# Bug 修复说明 - 文件上传重复弹出和 os 导入错误

## 修复的问题

### 问题 1: 文件选择器弹出两次

**症状**: 点击上传区域后，文件选择对话框会弹出两次

**原因**: 
- 点击 `uploadArea` 时触发 `fileInput.click()`
- 但 `fileInput` 的 `change` 事件也会触发上传
- 导致事件处理逻辑执行两次

**修复方案**:

在 [`templates/index.html`](file://c:\Users\aodon\Desktop\style_change_agent\templates\index.html#L800-L811) 中：

```javascript
// 修复前
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// 修复后
uploadArea.addEventListener('click', (e) => {
    e.stopPropagation();  // 阻止事件冒泡
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
        e.target.value = '';  // 重置 input 值，允许重复选择同一文件
    }
});
```

### 问题 2: os 模块导入错误

**症状**: 
```
分析失败：cannot access local variable 'os' where it is not associated with a value
```

**原因**:
- 在 `analyze_document()` 函数内部使用 `import os`
- Python 函数内部的 `import` 语句作用域问题
- `os` 模块已经在文件顶部导入，不需要在函数内部重复导入

**修复方案**:

在 [`style_extractor.py`](file://c:\Users\aodon\Desktop\style_change_agent\style_extractor.py#L594-L640) 中：

```python
# 修复前
if use_llm:
    try:
        import os  # ❌ 错误：在函数内部导入
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        ...

# 修复后
if use_llm:
    try:
        # 移除 import os，使用文件顶部的全局导入
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        ...
```

## 修改的文件

1. **templates/index.html** (第 800-811 行)
   - 添加 `e.stopPropagation()` 阻止事件冒泡
   - 添加 `e.target.value = ''` 重置文件输入

2. **style_extractor.py** (第 594-640 行)
   - 移除函数内部的 `import os`
   - 使用文件顶部的全局 `import os`

## 测试验证

### 测试 1: 文件上传不再重复弹出

1. 打开网页
2. 点击上传区域
3. ✅ 文件选择对话框应该只弹出一次
4. 选择文件后
5. ✅ 应该立即开始上传，不会重复处理

### 测试 2: API Key 错误不再出现

1. 确保 Railway 已设置 `DASHSCOPE_API_KEY` 环境变量
2. 上传一个 Word 文档
3. ✅ 不应该再出现 "cannot access local variable 'os'" 错误
4. ✅ 如果 API Key 正确，应该能看到 LLM 分析结果
5. ✅ 如果 API Key 未设置，应该显示 "未设置 DASHSCOPE_API_KEY 环境变量"

## 部署步骤

```bash
cd c:\Users\aodon\Desktop\style_change_agent
git add .
git commit -m "修复文件上传重复弹出和 os 导入错误"
git push
```

Railway 会自动检测 GitHub 推送并重新部署（约 2-3 分钟）。

## 其他改进建议

### 1. 更好的错误提示

目前错误通过 `alert()` 显示，可以考虑使用更优雅的 Toast 提示：

```javascript
function showToast(message, type = 'error') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}
```

### 2. 文件上传进度

可以添加上传进度条：

```javascript
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
    const percent = (e.loaded / e.total) * 100;
    updateProgressBar(percent);
});
```

### 3. 拖拽上传优化

可以添加视觉反馈：

```javascript
uploadArea.addEventListener('dragenter', () => {
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});
```

## 常见问题

### Q: 为什么文件选择器会弹出两次？

A: 因为点击事件和 change 事件都触发了上传逻辑。使用 `stopPropagation()` 可以阻止事件冒泡，避免重复触发。

### Q: 为什么不能在函数内部 import os？

A: 虽然 Python 允许在函数内部导入模块，但：
1. 导入的模块只在函数作用域内有效
2. 可能导致变量作用域混淆
3. 最佳实践是在文件顶部统一导入所有依赖

### Q: 重置 fileInput 的值有什么用？

A: 如果不重置，用户选择同一个文件后不会触发 `change` 事件。重置后可以确保每次选择文件都能触发事件。

## 验证清单

部署完成后，请检查：

- [ ] 点击上传区域，文件选择器只弹出一次
- [ ] 选择文件后立即开始上传，不会重复处理
- [ ] 可以重复选择同一个文件
- [ ] 不再出现 "cannot access local variable 'os'" 错误
- [ ] 如果 API Key 未设置，显示明确的错误信息
- [ ] 如果 API Key 正确，LLM 分析正常工作

如果还有问题，请查看浏览器控制台的错误信息。
