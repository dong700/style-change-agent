"""
Ollama 本地模型性能测试
测试三个模型的响应时间和质量
"""
import os
import sys
import json
import re
import time
import requests

# 强制刷新输出
import functools
print = functools.partial(print, flush=True)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 600  # 10分钟

# 测试文本
TEST_TEXT = """
人工智能技术的快速发展正在深刻改变我们的生活方式。从智能手机的语音助手到自动驾驶汽车，
AI已经渗透到日常生活的方方面面。然而，随着技术的进步，我们也面临着新的挑战：
如何确保AI的安全性和可控性？如何平衡技术发展与隐私保护？这些问题需要我们深入思考。
"""

PROMPT = f"""你是一位专业的文本风格分析专家。请对以下文本进行风格分析。

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
{TEST_TEXT}

请直接输出 JSON 格式结果："""


def check_ollama_status():
    """检查 Ollama 服务状态"""
    print("=" * 60)
    print("检查 Ollama 服务状态")
    print("=" * 60)
    
    try:
        print(f"正在连接 {OLLAMA_BASE_URL} ...")
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=30)
        if response.status_code == 200:
            data = response.json()
            models = [m.get('name', '') for m in data.get('models', [])]
            print(f"[OK] Ollama 服务运行正常")
            print(f"[OK] 可用模型: {models}")
            return True, models
        else:
            print(f"[FAIL] Ollama 服务返回错误: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"[FAIL] 连接失败: {e}")
        return False, []


def test_model(model: str):
    """测试单个模型"""
    print(f"\n{'#' * 60}")
    print(f"测试模型: {model}")
    print("#" * 60)
    
    print(f"开始时间: {time.strftime('%H:%M:%S')}")
    start_time = time.time()
    
    try:
        print(f"正在发送请求到 Ollama...")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": PROMPT,
                "stream": False,
                "options": {
                    "num_predict": 2000,
                    "temperature": 0.7
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        print(f"收到响应，耗时: {elapsed_time:.2f} 秒")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            print(f"响应状态码: 200")
            print(f"响应长度: {len(response_text)} 字符")
            
            if response_text and response_text.strip():
                # 显示响应内容前200字符
                print(f"响应内容预览: {response_text[:200]}...")
                
                # 尝试解析 JSON
                json_success = False
                try:
                    json_text = response_text.strip()
                    if '```json' in json_text:
                        match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
                        if match:
                            json_text = match.group(1).strip()
                    elif '```' in json_text:
                        match = re.search(r'```\s*(.*?)\s*```', json_text, re.DOTALL)
                        if match:
                            json_text = match.group(1).strip()
                    
                    if not json_text.startswith('{'):
                        match = re.search(r'\{.*\}', json_text, re.DOTALL)
                        if match:
                            json_text = match.group(0).strip()
                    
                    parsed = json.loads(json_text)
                    json_success = True
                    print(f"JSON解析: 成功")
                except Exception as e:
                    print(f"JSON解析: 失败 - {e}")
                
                print(f"\n[OK] 模型 {model} 测试成功!")
                print(f"     总耗时: {elapsed_time:.2f} 秒")
                
                return {
                    'model': model,
                    'success': True,
                    'time': elapsed_time,
                    'chars': len(response_text),
                    'json_ok': json_success
                }
            else:
                print(f"[FAIL] 返回内容为空")
                return {
                    'model': model,
                    'success': False,
                    'time': elapsed_time,
                    'error': '返回内容为空'
                }
        else:
            print(f"[FAIL] API 错误: {response.status_code}")
            print(f"错误详情: {response.text[:500]}")
            return {
                'model': model,
                'success': False,
                'time': elapsed_time,
                'error': f'API错误: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"[FAIL] 超时 (>{OLLAMA_TIMEOUT}秒)")
        return {
            'model': model,
            'success': False,
            'time': elapsed_time,
            'error': '超时'
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[FAIL] 错误: {e}")
        import traceback
        traceback.print_exc()
        return {
            'model': model,
            'success': False,
            'time': elapsed_time,
            'error': str(e)
        }


def main():
    print("\n" + "=" * 60)
    print("Ollama 模型性能测试")
    print("=" * 60)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查服务
    ok, available_models = check_ollama_status()
    if not ok:
        print("\n请先启动 Ollama: ollama serve")
        return
    
    # 要测试的模型
    test_models = ['qwen3.5:2b', 'qwen3.5:4b', 'deepseek-r1:7b']
    
    # 过滤出可用的模型
    models_to_test = []
    for m in test_models:
        if m in available_models or f"{m}:latest" in available_models:
            models_to_test.append(m)
        else:
            print(f"\n[WARN] 模型 {m} 未安装，跳过")
    
    if not models_to_test:
        print("\n没有可测试的模型")
        return
    
    print(f"\n将测试 {len(models_to_test)} 个模型: {models_to_test}")
    
    # 测试每个模型
    results = []
    for i, model in enumerate(models_to_test):
        print(f"\n>>> 进度: {i+1}/{len(models_to_test)}")
        result = test_model(model)
        results.append(result)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"{'模型':<20} {'状态':<8} {'耗时(秒)':<12} {'字符数':<10} {'JSON':<8}")
    print("-" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    for r in results:
        status = "成功" if r['success'] else "失败"
        chars = str(r.get('chars', '-'))
        json_status = "OK" if r.get('json_ok') else "-"
        print(f"{r['model']:<20} {status:<8} {r['time']:<12.2f} {chars:<10} {json_status:<8}")
    
    # 找出最快的成功模型
    if successful:
        fastest = min(successful, key=lambda x: x['time'])
        print(f"\n[推荐] 最快模型: {fastest['model']} ({fastest['time']:.2f}秒)")
    else:
        print(f"\n[WARN] 所有模型都失败了")
    
    print(f"\n结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
