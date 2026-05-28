"""
测试 DeepSeek API 调用
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from style_extractor import LLMStyleAnalyzer

API_KEY = "sk-94b290c6b6324c36b8da09cc479c009e"

def test_deepseek_api():
    print("=" * 60)
    print("测试 DeepSeek API 调用")
    print("=" * 60)
    
    # 测试文本
    test_text = """
    国立中正大学筹办过程中，熊式辉主持筹办工作，将国立中正大学筹办列为其政务的头等大事。
    他雷厉风行地推进各项筹备工作，同时十分注重延揽人才，亲自出面聘请了一批知名学者担任教授。
    """
    
    # 测试两个模型
    models = ['deepseek-api:deepseek-v4-flash', 'deepseek-api:deepseek-v4-pro']
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"测试模型: {model}")
        print(f"{'='*60}")
        
        try:
            analyzer = LLMStyleAnalyzer(model=model, deepseek_api_key=API_KEY)
            
            import time
            start = time.time()
            
            result = analyzer.analyze(test_text)
            
            elapsed = time.time() - start
            
            print(f"\n调用成功! 耗时: {elapsed:.2f} 秒")
            print(f"\n风格标签数量: {len(result.get('style_labels', []))}")
            
            for label in result.get('style_labels', [])[:5]:
                print(f"  - {label.get('label', 'N/A')}: {label.get('score', 'N/A')}分")
            
            print(f"\n总结: {result.get('overall_style_summary', 'N/A')[:100]}...")
            
        except Exception as e:
            print(f"\n调用失败: {e}")
    
    print(f"\n{'='*60}")
    print("测试完成!")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_deepseek_api()
