"""
风格索引 - 建立索引并支持智能检索
"""
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("警告：FAISS 未安装，将使用简单的相似度计算。建议安装：pip install faiss-cpu")


class StyleIndex:
    """风格索引系统"""
    
    def __init__(self, use_faiss: bool = True):
        """
        初始化风格索引
        
        Args:
            use_faiss: 是否使用 FAISS 加速检索
        """
        self.fragments = []
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.semantic_index = None
        self.topic_index = defaultdict(list)
        self.chapter_index = defaultdict(list)
        self.global_style = None
    
    def build_index(self, fragments: List[Dict[str, Any]]):
        """
        建立索引
        
        Args:
            fragments: 包含风格特征的片段列表
        """
        print(f"建立索引，共 {len(fragments)} 个片段...")
        
        self.fragments = fragments
        
        for i, fragment in enumerate(fragments):
            fragment['index'] = i
            
            if 'style_features' in fragment:
                topic_tags = fragment['style_features'].get('topic_tags', [])
                for tag in topic_tags:
                    self.topic_index[tag].append(i)
            
            chapter = fragment.get('chapter', '未知章节')
            self.chapter_index[chapter].append(i)
        
        if self.use_faiss:
            self._build_faiss_index()
        
        self._compute_global_style()
        
        print("索引建立完成！")
    
    def _build_faiss_index(self):
        """构建 FAISS 索引"""
        vectors = []
        
        for fragment in self.fragments:
            if 'style_features' in fragment:
                quant = fragment['style_features'].get('quantitative', {})
                vector = self._create_feature_vector(quant)
                vectors.append(vector)
        
        if not vectors:
            return
        
        vectors_array = np.array(vectors, dtype='float32')
        
        dimension = vectors_array.shape[1]
        self.semantic_index = faiss.IndexFlatL2(dimension)
        self.semantic_index.add(vectors_array)
        
        print(f"FAISS 索引构建完成，维度：{dimension}")
    
    def _create_feature_vector(self, quantitative_features: Dict) -> List[float]:
        """创建特征向量"""
        vector = []
        
        syntax = quantitative_features.get('句法特征', {})
        vector.extend([
            syntax.get('平均句长', 0) / 100,
            syntax.get('句长标准差', 0) / 100,
            syntax.get('平均从句数', 0) / 10,
            syntax.get('标点密度', 0) / 100
        ])
        
        lexical = quantitative_features.get('词汇特征', {})
        vector.extend([
            lexical.get('词汇丰富度', 0),
            lexical.get('高频词占比', 0) / 100,
            lexical.get('人称代词占比', 0) / 100,
            lexical.get('情态动词密度', 0) / 100
        ])
        
        readability = quantitative_features.get('可读性特征', {})
        vector.extend([
            readability.get('Flesch-Kincaid 等级', 0) / 100,
            readability.get('被动语态比例', 0) / 100,
            readability.get('连词密度', 0) / 100
        ])
        
        return vector
    
    def _compute_global_style(self):
        """计算全局风格"""
        if not self.fragments:
            return
        
        all_style_labels = []
        all_quantitative = []
        
        for fragment in self.fragments:
            if 'style_features' in fragment:
                llm_analysis = fragment['style_features'].get('llm_analysis', {})
                if 'style_labels' in llm_analysis:
                    all_style_labels.extend(llm_analysis['style_labels'])
                
                quant = fragment['style_features'].get('quantitative', {})
                if quant:
                    all_quantitative.append(quant)
        
        self.global_style = {
            'style_labels': self._aggregate_style_labels(all_style_labels),
            'avg_quantitative': self._average_quantitative(all_quantitative),
            'example_fragments': [f['text'][:200] + '...' if len(f['text']) > 200 else f['text'] for f in self.fragments[:5]],
            'total_fragments': len(self.fragments),
            'fragments_with_style': len([f for f in self.fragments if 'style_features' in f])
        }
    
    def _aggregate_style_labels(self, style_labels: List[Dict]) -> List[Dict]:
        """聚合风格标签"""
        label_scores = defaultdict(list)
        
        for label in style_labels:
            label_name = label.get('label', '')
            score = label.get('score', 0)
            # 确保 score 是数字类型
            try:
                score = float(score) if score else 0
            except (ValueError, TypeError):
                score = 0
            label_scores[label_name].append(score)
        
        aggregated = []
        for label_name, scores in label_scores.items():
            # 过滤掉无效的分数
            valid_scores = [s for s in scores if isinstance(s, (int, float))]
            if not valid_scores:
                continue
            avg_score = sum(valid_scores) / len(valid_scores)
            if avg_score >= 3.0:
                aggregated.append({
                    'label': label_name,
                    'score': round(avg_score, 1),
                    'frequency': len(valid_scores)
                })
        
        aggregated.sort(key=lambda x: x['score'], reverse=True)
        return aggregated[:20]
    
    def _average_quantitative(self, quantitative_list: List[Dict]) -> Dict:
        """计算平均量化特征"""
        if not quantitative_list:
            return {}
        
        avg_features = {}
        
        feature_keys = [
            ('句法特征', ['平均句长', '句长标准差', '平均从句数', '标点密度']),
            ('词汇特征', ['词汇丰富度', '高频词占比', '人称代词占比', '情态动词密度']),
            ('可读性特征', ['Flesch-Kincaid 等级', '被动语态比例', '连词密度'])
        ]
        
        for category, keys in feature_keys:
            avg_features[category] = {}
            for key in keys:
                values = [q.get(category, {}).get(key, 0) for q in quantitative_list]
                avg_features[category][key] = sum(values) / len(values)
        
        return avg_features
    
    def search_similar(self, query_fragment: Dict[str, Any], 
                      top_k: int = 3,
                      threshold: float = 0.75) -> List[Dict[str, Any]]:
        """
        检索相似的片段
        
        Args:
            query_fragment: 查询片段
            top_k: 返回前 K 个结果
            threshold: 相似度阈值
            
        Returns:
            List[Dict]: 相似片段列表
        """
        results = []
        
        if self.use_faiss and self.semantic_index is not None:
            query_vector = self._create_feature_vector(
                query_fragment.get('style_features', {}).get('quantitative', {})
            )
            query_array = np.array([query_vector], dtype='float32')
            
            distances, indices = self.semantic_index.search(query_array, top_k * 2)
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.fragments):
                    similarity = 1 / (1 + dist)
                    if similarity >= threshold:
                        fragment = self.fragments[idx].copy()
                        fragment['similarity'] = similarity
                        results.append(fragment)
        
        if len(results) < top_k:
            topic_results = self._search_by_topic(query_fragment, top_k - len(results))
            results.extend(topic_results)
        
        return results[:top_k]
    
    def _search_by_topic(self, query_fragment: Dict[str, Any], 
                        top_k: int) -> List[Dict[str, Any]]:
        """通过主题标签检索"""
        results = []
        
        query_tags = query_fragment.get('style_features', {}).get('topic_tags', [])
        
        matched_indices = []
        for tag in query_tags:
            matched_indices.extend(self.topic_index.get(tag, []))
        
        seen = set()
        for idx in matched_indices:
            if idx not in seen and len(results) < top_k:
                fragment = self.fragments[idx].copy()
                fragment['similarity'] = 0.6
                results.append(fragment)
                seen.add(idx)
        
        return results
    
    def get_fallback_style(self) -> Dict[str, Any]:
        """获取兜底风格"""
        return self.global_style
    
    def save_index(self, output_path: str):
        """保存索引"""
        data = {
            'fragments': self.fragments,
            'topic_index': dict(self.topic_index),
            'chapter_index': dict(self.chapter_index),
            'global_style': self.global_style
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if self.use_faiss and self.semantic_index is not None:
            faiss_path = output_path.replace('.json', '.faiss')
            faiss.write_index(self.semantic_index, faiss_path)
    
    def load_index(self, input_path: str):
        """加载索引"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.fragments = data['fragments']
        self.topic_index = defaultdict(list, data['topic_index'])
        self.chapter_index = defaultdict(list, data['chapter_index'])
        self.global_style = data['global_style']
        
        if self.use_faiss:
            faiss_path = input_path.replace('.json', '.faiss')
            if os.path.exists(faiss_path):
                self.semantic_index = faiss.read_index(faiss_path)
            else:
                self._build_faiss_index()
