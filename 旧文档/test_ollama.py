"""
Ollama 本地模型调用测试脚本
测试内容：
1. Ollama 服务连接
2. 模型可用性检查
3. 风格分析调用
4. JSON 解析
"""
import os
import sys
import json
import re

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 1200  # 20分钟


def test_ollama_connection():
    """测试 Ollama 服务连接"""
    import requests
    
    print("=" * 60)
    print("测试 1: Ollama 服务连接")
    print("=" * 60)
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=30)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"[OK] Ollama 服务运行正常")
            print(f"[OK] 可用模型: {[m.get('name') for m in models]}")
            return True, models
        else:
            print(f"[FAIL] Ollama 服务返回错误: {response.status_code}")
            return False, []
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] 无法连接到 Ollama 服务 ({OLLAMA_BASE_URL})")
        print("  请确保 Ollama 已启动，在终端运行: ollama serve")
        return False, []
    except Exception as e:
        print(f"[FAIL] 连接错误: {e}")
        return False, []


def test_ollama_call(model: str, prompt: str):
    """测试 Ollama 模型调用"""
    import requests
    
    print(f"\n{'=' * 60}")
    print(f"测试 2: 调用 Ollama 模型 {model}")
    print("=" * 60)
    
    try:
        print(f"正在调用模型（超时时间: {OLLAMA_TIMEOUT}秒）...")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 2000,
                    "temperature": 0.7
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            if response_text:
                print(f"[OK] 调用成功，返回 {len(response_text)} 字符")
                return True, response_text
            else:
                print("[FAIL] 返回内容为空")
                return False, ""
        else:
            print(f"[FAIL] API 调用失败: {response.status_code}")
            print(f"  错误详情: {response.text[:500]}")
            return False, ""
            
    except requests.exceptions.Timeout:
        print(f"[FAIL] 调用超时（超过 {OLLAMA_TIMEOUT} 秒）")
        return False, ""
    except Exception as e:
        print(f"[FAIL] 调用错误: {e}")
        return False, ""


def extract_json(response_text: str) -> dict:
    """从响应文本中提取 JSON"""
    print(f"\n{'=' * 60}")
    print("测试 3: JSON 解析")
    print("=" * 60)
    
    if not response_text:
        print("[FAIL] 响应文本为空")
        return None
    
    print(f"原始响应（前300字符）:\n{response_text[:300]}...")
    
    json_text = response_text.strip()
    
    # 格式1: ```json ... ```
    if '```json' in response_text:
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1).strip()
            print("[OK] 检测到 ```json 格式")
    
    # 格式2: ``` ... ```
    elif '```' in response_text:
        json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1).strip()
            print("[OK] 检测到 ``` 格式")
    
    # 格式3: 查找 { ... } 的JSON对象
    if not json_text.startswith('{'):
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0).strip()
            print("[OK] 从文本中提取 JSON 对象")
    
    # 格式4: 移除可能的前缀文本
    if '{' in json_text and not json_text.startswith('{'):
        start_idx = json_text.find('{')
        json_text = json_text[start_idx:]
        print("[OK] 移除前缀文本")
    
    try:
        result = json.loads(json_text)
        print("[OK] JSON 解析成功")
        return result
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON 解析失败: {e}")
        print(f"尝试解析的内容（前500字符）:\n{json_text[:500]}")
        return None


def test_style_analysis(model: str):
    """测试完整的风格分析流程"""
    print(f"\n{'=' * 60}")
    print("测试 4: 完整风格分析流程")
    print("=" * 60)
    
    # 测试文本
    test_text = """
    人工智能技术的快速发展正在深刻改变我们的生活方式。从智能手机的语音助手到自动驾驶汽车，
    AI已经渗透到日常生活的方方面面。然而，随着技术的进步，我们也面临着新的挑战：
    如何确保AI的安全性和可控性？如何平衡技术发展与隐私保护？这些问题需要我们深入思考。
    """
    
    prompt = f"""你是一位专业的文本风格分析专家。请对以下文本进行风格分析。

【输出格式】
请严格按照以下 JSON 结构输出，不要添加任何解释：
{{
  "dimensions": {{
    "词汇风格": [{{"label": "标签名", "score": 整数 1-5, "evidence": "依据文本片段"}}],
    "句法风格": [{{"label": "标签名", "score": 整数 1-5, "evidence": "依据文本片段"}}]
  }},
  "summary": "整体风格描述"
}}

【待分析文本】
{test_text}

请直接输出 JSON 格式结果："""
    
    # 调用模型
    success, response_text = test_ollama_call(model, prompt)
    
    if not success:
        return False
    
    # 解析 JSON
    result = extract_json(response_text)
    
    if result:
        print(f"\n[OK] 风格分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    else:
        return False


def main():
    print("\n" + "=" * 60)
    print("Ollama 本地模型测试")
    print("=" * 60)
    
    # 测试1: 连接
    connected, models = test_ollama_connection()
    if not connected:
        print("\n[FAIL] 测试失败: Ollama 服务未运行")
        print("请先启动 Ollama: ollama serve")
        return
    
    # 检查模型
    model_names = [m.get('name', '') for m in models]
    test_models = []
    
    if 'qwen3.5:4b' in model_names or 'qwen3.5:4b:latest' in model_names:
        test_models.append('qwen3.5:4b')
    if 'qwen3.5:2b' in model_names or 'qwen3.5:2b:latest' in model_names:
        test_models.append('qwen3.5:2b')
    
    if not test_models:
        print("\n[WARN] 未找到 qwen3.5:4b 或 qwen3.5:2b 模型")
        print("请先下载模型: ollama pull qwen3.5:4b")
        return
    
    print(f"\n将测试模型: {test_models}")
    
    # 测试每个模型
    for model in test_models:
        print(f"\n{'#' * 60}")
        print(f"测试模型: {model}")
        print("#" * 60)
        
        success = test_style_analysis(model)
        
        if success:
            print(f"\n[PASS] 模型 {model} 测试通过")
        else:
            print(f"\n[FAIL] 模型 {model} 测试失败")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
