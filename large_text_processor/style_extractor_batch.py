"""
批量风格提取器 - 提取片段的风格特征（带缓存功能）
"""
import os
import sys
import json
import hashlib
from typing import List, Dict, Any
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from style_extractor import LLMStyleAnalyzer, StyleExtractor


class BatchStyleExtractor:
    """批量风格提取器（带缓存）"""
    
    def __init__(self, model: str = "qwen-plus", cache_dir: str = None, deepseek_api_key: str = ''):
        """
        初始化批量风格提取器
        
        Args:
            model: 使用的模型名称
            cache_dir: 缓存目录，默认为 outputs/style_cache
            deepseek_api_key: DeepSeek API Key（前端传入）
        """
        self.model = model
        self.llm_analyzer = LLMStyleAnalyzer(model=model, deepseek_api_key=deepseek_api_key)
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'outputs', 'style_cache'
        )
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_text_hash(self, text: str) -> str:
        """生成文本的哈希值作为缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, text_hash: str) -> str:
        """获取缓存文件路径"""
        # 替换文件名中的非法字符（Windows不允许冒号）
        safe_model_name = self.model.replace(':', '_').replace('/', '_')
        return os.path.join(self.cache_dir, f"{text_hash}_{safe_model_name}.json")
    
    def _load_from_cache(self, text: str) -> Dict[str, Any]:
        """从缓存加载风格分析结果"""
        text_hash = self._get_text_hash(text)
        cache_path = self._get_cache_path(text_hash)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载缓存失败: {e}")
        
        return None
    
    def _save_to_cache(self, text: str, result: Dict[str, Any]):
        """保存风格分析结果到缓存"""
        text_hash = self._get_text_hash(text)
        cache_path = self._get_cache_path(text_hash)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def extract_batch(self, fragments: List[Dict[str, Any]], 
                     batch_size: int = 5,
                     save_progress: bool = True,
                     progress_file: str = None) -> List[Dict[str, Any]]:
        """
        批量提取片段的风格特征（带缓存）
        
        Args:
            fragments: 片段列表
            batch_size: 批处理大小
            save_progress: 是否保存进度
            progress_file: 进度文件路径
            
        Returns:
            List[Dict]: 包含风格特征的片段列表
        """
        results = []
        total = len(fragments)
        
        # 尝试加载之前的进度
        start_index = 0
        if progress_file and os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    results = progress_data.get('results', [])
                    start_index = len(results)
                    print(f"从缓存恢复进度：已处理 {start_index}/{total} 个片段")
            except Exception as e:
                print(f"加载进度失败: {e}")
        
        # 统计缓存命中
        cache_hits = 0
        
        print(f"开始提取 {total} 个片段的风格特征（从第 {start_index + 1} 个开始）...")
        
        # 减少 tqdm 输出频率，mininterval=10 表示每10秒更新一次
        for i in tqdm(range(start_index, total, batch_size), desc="风格提取", mininterval=10):
            batch = fragments[i:i+batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
            
            if save_progress and progress_file:
                self._save_progress(results, progress_file, i + batch_size, total)
        
        print(f"风格提取完成！共处理 {len(results)} 个片段")
        return results
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理一批片段（带缓存）"""
        results = []
        
        for fragment in batch:
            try:
                text = fragment['text']
                
                # 先尝试从缓存加载
                cached_result = self._load_from_cache(text)
                
                if cached_result:
                    result = fragment.copy()
                    result['style_features'] = cached_result
                    result['from_cache'] = True
                    results.append(result)
                    continue
                
                # 没有缓存，进行提取
                extractor = StyleExtractor(text)
                quantitative_features = extractor.extract_all_features()
                
                llm_result = self.llm_analyzer.analyze(
                    text, 
                    max_length=min(len(text), 2000)
                )
                
                topic_tags = self._extract_topic_tags(text)
                
                style_features = {
                    'quantitative': quantitative_features,
                    'llm_analysis': llm_result,
                    'topic_tags': topic_tags
                }
                
                # 保存到缓存
                self._save_to_cache(text, style_features)
                
                result = fragment.copy()
                result['style_features'] = style_features
                result['from_cache'] = False
                
                results.append(result)
                
            except Exception as e:
                import traceback
                print(f"\n处理片段 {fragment.get('id', 'unknown')} 时出错：{e}")
                traceback.print_exc()
                result = fragment.copy()
                result['style_features'] = {
                    'error': str(e)
                }
                results.append(result)
        
        return results
    
    def _extract_topic_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """提取主题标签"""
        from style_extractor import StyleExtractor
        
        extractor = StyleExtractor(text)
        word_freq = extractor.get_word_frequency(top_n=20)
        
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人'}
        
        topic_words = []
        for word, count in word_freq.items():
            if word not in stop_words and len(word) >= 2:
                topic_words.append(word)
                if len(topic_words) >= max_tags:
                    break
        
        return topic_words
    
    def _save_progress(self, results: List[Dict], file_path: str, 
                      processed: int, total: int):
        """保存进度"""
        data = {
            'progress': {
                'processed': processed,
                'total': total,
                'percentage': round(processed / total * 100, 2) if total > 0 else 0
            },
            'model': self.model,
            'results': results
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_progress(self, file_path: str) -> Dict[str, Any]:
        """加载进度"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_results(self, results: List[Dict], output_path: str):
        """保存结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_fragments': len(results),
                'model': self.model,
                'fragments': results
            }, f, ensure_ascii=False, indent=2)
    
    def clear_cache(self):
        """清空缓存"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            print(f"已清空缓存目录: {self.cache_dir}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
        return {
            'total_cache_files': len(cache_files),
            'cache_dir': self.cache_dir
        }
