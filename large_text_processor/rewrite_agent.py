"""
改写 Agent - 智能改写片段
"""
import os
import sys
import json
import re
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from style_rewriter import StyleRewriter


class RewriteAgent:
    """改写 Agent"""
    
    def __init__(self, model: str = "deepseek-api:deepseek-v4-flash", deepseek_api_key: str = ''):
        """
        初始化改写 Agent
        
        Args:
            model: 使用的模型名称
            deepseek_api_key: DeepSeek API Key
        """
        self.model = model
        self.deepseek_api_key = deepseek_api_key
        self.rewriter = StyleRewriter(model=model, deepseek_api_key=deepseek_api_key)
    
    def rewrite_batch(self, target_fragments: List[Dict[str, Any]],
                     style_index: 'StyleIndex',
                     batch_size: int = 5,
                     save_progress: bool = True,
                     progress_file: str = None) -> List[Dict[str, Any]]:
        """
        批量改写片段
        
        Args:
            target_fragments: 目标片段列表
            style_index: 风格索引
            batch_size: 批处理大小
            save_progress: 是否保存进度
            progress_file: 进度文件路径
            
        Returns:
            List[Dict]: 改写结果列表
        """
        results = []
        total = len(target_fragments)
        
        print(f"开始改写 {total} 个片段...")
        
        for i in range(0, total, batch_size):
            batch = target_fragments[i:i+batch_size]
            batch_results = self._process_batch(batch, style_index)
            results.extend(batch_results)
            
            if save_progress and progress_file:
                self._save_progress(results, progress_file, i + batch_size, total)
        
        print(f"改写完成！共处理 {len(results)} 个片段")
        return results
    
    def _process_batch(self, batch: List[Dict[str, Any]], 
                      style_index: 'StyleIndex') -> List[Dict[str, Any]]:
        """处理一批片段"""
        results = []
        
        for fragment in batch:
            try:
                similar_fragments = style_index.search_similar(fragment, top_k=3)
                
                if similar_fragments:
                    best_match = similar_fragments[0]
                    style_labels = best_match.get('style_features', {}).get('llm_analysis', {}).get('style_labels', [])
                    example_fragments = [f['text'] for f in similar_fragments[:2]]
                    match_type = 'high_similarity'
                    confidence = best_match.get('similarity', 0.8)
                else:
                    fallback_style = style_index.get_fallback_style()
                    style_labels = fallback_style.get('style_labels', [])
                    example_fragments = fallback_style.get('example_fragments', [])
                    match_type = 'global_fallback'
                    confidence = 0.5
                
                rewritten_text = self._rewrite_with_examples(
                    target_text=fragment['text'],
                    style_labels=style_labels,
                    example_fragments=example_fragments
                )
                
                result = {
                    'fragment_id': fragment['id'],
                    'original_text': fragment['text'],
                    'rewritten_text': rewritten_text,
                    'chapter': fragment.get('chapter', ''),
                    'style_match': {
                        'match_type': match_type,
                        'confidence': confidence,
                        'reference_count': len(similar_fragments)
                    }
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"\n改写片段 {fragment['id']} 时出错：{e}")
                result = {
                    'fragment_id': fragment['id'],
                    'original_text': fragment['text'],
                    'rewritten_text': fragment['text'],
                    'error': str(e),
                    'chapter': fragment.get('chapter', '')
                }
                results.append(result)
        
        return results
    
    def _rewrite_with_examples(self, target_text: str,
                               style_labels: List[Dict],
                               example_fragments: List[str]) -> str:
        """使用示例改写"""
        from langchain_community.llms.tongyi import Tongyi
        
        llm = Tongyi(model=self.model)
        
        prompt = f"""你是一位专业的文本改写专家。请根据提供的风格示例，将目标文本改写成相似的风格。

【风格示例】
{chr(10).join([f'{i+1}. {frag}' for i, frag in enumerate(example_fragments[:2])])}

【风格标签】
{self._format_style_labels(style_labels[:10])}

【目标文本】（需要改写的原文）
{target_text}

【改写要求】
1. 保持原文的核心事实和数据不变
2. 学习风格示例的表达方式和句式结构
3. 不要引入风格示例中的具体内容（如人名、地名、事件）
4. 改写后长度与原文相当（±20%）
5. 语言自然流畅

请直接输出改写后的文本："""

        response = llm.invoke(prompt)
        return response.strip()
    
    def _format_style_labels(self, style_labels: List[Dict]) -> str:
        """格式化风格标签"""
        formatted = []
        for i, label in enumerate(style_labels, 1):
            label_name = label.get('label', '未知')
            score = label.get('score', 0)
            stars = '⭐' * int(score) + '☆' * (5 - int(score))
            formatted.append(f"{i}. {label_name} {stars}")
        
        return '\n'.join(formatted)
    
    def _save_progress(self, results: List[Dict], file_path: str,
                      processed: int, total: int):
        """保存进度"""
        data = {
            'progress': {
                'processed': processed,
                'total': total,
                'percentage': round(processed / total * 100, 2)
            },
            'results': results
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_results(self, results: List[Dict], output_path: str):
        """保存结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_fragments': len(results),
                'model': self.model,
                'results': results
            }, f, ensure_ascii=False, indent=2)
