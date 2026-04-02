"""
文章风格特征提取器
用于从 Word 文档中提取可量化的写作风格参数
仅支持中文文本
输出 JSON 格式结果到文件
"""

import os
import re
import statistics
import json
from collections import Counter
from typing import Dict, List, Any
from docx import Document
import jieba

# 尝试导入 LLM 相关库
try:
    from langchain_community.llms.tongyi import Tongyi
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告：langchain-community 未安装，LLM 分析功能将不可用")
    print("请运行：pip install langchain-community")

# 配置项
配置 = {
    '输出目录': 'output',
    '示例目录': r"c:\Users\aodon\Desktop\style_change_agent\data\example",
    '最大词频数': 100,
    '句子最大长度': 2000,
    '模型名称': 'qwen-max'
}

# NLTK 资源已移除，仅使用中文分词

class StyleExtractor:
    """文章风格特征提取器（仅支持中文）"""
    
    def __init__(self, text: str):
        """
        初始化风格提取器
        
        Args:
            text: 输入的文本内容（中文）
        """
        self.text = text
        # 中文分句
        self.sentences = re.split(r'[。！？.!?]', text)
        self.sentences = [s.strip() for s in self.sentences if s.strip()]
        # 中文分词
        self.words = list(jieba.cut(text))
        self.words = [w.strip() for w in self.words if w.strip()]
        self.words_lower = [w.lower() for w in self.words]
        self.pos_tags = []  # 中文暂不支持词性标注
        
        # 停用词（中文）
        self.stop_words_cn = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '可以'
        }
        
        # 人称代词（中文）
        self.personal_pronouns = {
            '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
            '我的', '你的', '他的', '她的', '它的', '我们的', '你们的', '他们的', '她们的', '它们的'
        }
        
        # 情态动词（中文）
        self.modal_verbs = {
            '能', '能够', '可以', '可能', '会', '应该', '必须', '将', '要', '愿', '肯', '敢'
        }
        
        # 连词（中文）
        self.conjunctions = {
            '和', '与', '及', '或', '但', '但是', '而', '而且', '并且', '如果',
            '虽然', '因为', '所以', '因此', '于是', '然而', '可是', '尽管', '即使', '既然'
        }
        
        # 高频词（前 50 个最常见词）
        self.common_words = set(self.words_lower[:50]) if len(self.words) > 50 else set(self.words_lower)
    
    def extract_syntax_features(self) -> Dict[str, float]:
        """
        提取句法特征
        
        Returns:
            包含句法特征的字典
        """
        # 平均句长（词数）
        sentence_lengths = [len(sent) for sent in self.sentences]
        avg_sentence_length = statistics.mean(sentence_lengths) if sentence_lengths else 0
        
        # 句长标准差
        sentence_length_std = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # 平均从句数（通过标点符号和连词估算）
        clause_counts = []
        for sent in self.sentences:
            # 通过逗号和连词估算从句数
            conjunction_count = sum(1 for w in self.words if w in self.conjunctions)
            comma_count = sent.count(',')
            clause_count = 1 + conjunction_count + (comma_count / 2)
            clause_counts.append(clause_count)
        
        avg_clause_count = statistics.mean(clause_counts) if clause_counts else 0
        
        # 标点密度（每 100 词的标点符号数）
        punctuation = set('.,;:!?()[]{}"\'-')
        punctuation_count = sum(1 for w in self.words if w in punctuation)
        punctuation_density = (punctuation_count / len(self.words) * 100) if self.words else 0
        
        return {
            '平均句长': round(avg_sentence_length, 2),
            '句长标准差': round(sentence_length_std, 2),
            '平均从句数': round(avg_clause_count, 2),
            '标点密度': round(punctuation_density, 2)
        }
    
    def extract_lexical_features(self) -> Dict[str, float]:
        """
        提取词汇特征
        
        Returns:
            包含词汇特征的字典
        """
        # 词汇丰富度（不同词数/总词数）
        unique_words = set(self.words_lower)
        lexical_richness = len(unique_words) / len(self.words) if self.words else 0
        
        # 词性分布（中文暂不支持）
        pos_distribution = {}
        
        # 高频词占比
        content_words = [w for w in self.words_lower if w and w not in self.stop_words_cn]
        common_word_count = sum(1 for w in content_words if w in self.common_words)
        common_word_ratio = (common_word_count / len(content_words) * 100) if content_words else 0
        
        # 人称代词占比
        pronoun_count = sum(1 for w in self.words_lower if w in self.personal_pronouns)
        pronoun_ratio = (pronoun_count / len(self.words) * 100) if self.words else 0
        
        # 情态动词密度
        modal_count = sum(1 for w in self.words_lower if w in self.modal_verbs)
        modal_density = (modal_count / len(self.words) * 100) if self.words else 0
        
        return {
            '词汇丰富度': round(lexical_richness, 4),
            '词性分布': pos_distribution,
            '高频词占比': round(common_word_ratio, 2),
            '人称代词占比': round(pronoun_ratio, 2),
            '情态动词密度': round(modal_density, 2)
        }
    
    def extract_readability_features(self) -> Dict[str, float]:
        """
        提取可读性特征
        
        Returns:
            包含可读性特征的字典
        """
        # 中文使用简单的可读性指标：平均句长
        fk_grade = len(self.text) / len(self.sentences) if self.sentences else 0
        
        # 被动语态比例（通过"被"字）
        passive_count = self.text.count('被')
        total_verbs = len([w for w in self.words if w in ['是', '有', '在', '被', '把', '对']])
        passive_ratio = (passive_count / total_verbs * 100) if total_verbs else 0
        
        # 连词密度
        conjunction_count = sum(1 for w in self.words_lower if w in self.conjunctions)
        conjunction_density = (conjunction_count / len(self.words) * 100) if self.words else 0
        
        return {
            'Flesch-Kincaid 等级': round(fk_grade, 2),
            '被动语态比例': round(passive_ratio, 2),
            '连词密度': round(conjunction_density, 2)
        }
    
    def extract_rhythm_features(self) -> Dict[str, float]:
        """
        提取韵律特征
        
        Returns:
            包含韵律特征的字典
        """
        # 平均词长（字符数）
        word_lengths = [len(w) for w in self.words if w and any('\u4e00' <= c <= '\u9fff' for c in w)]
        avg_word_length = statistics.mean(word_lengths) if word_lengths else 0
        
        # 音节数分布（中文以字为单位，每个汉字一个音节）
        # 中文字符数即为音节数
        chinese_chars = [c for c in self.text if '\u4e00' <= c <= '\u9fff']
        syllable_counts = [1] * len(chinese_chars)
        avg_syllables = 1.0
        
        # 分布统计
        if syllable_counts:
            syllable_distribution = Counter(syllable_counts)
            total_syllable_words = sum(syllable_distribution.values())
            syllable_dist_percent = {
                f'{syl}_syllables': round(count / total_syllable_words * 100, 2)
                for syl, count in syllable_distribution.items()
            }
        else:
            syllable_dist_percent = {}
        
        return {
            '平均词长': round(avg_word_length, 2),
            '平均每词音节数': round(avg_syllables, 2),
            '音节分布': syllable_dist_percent
        }
    
    def extract_structure_features(self) -> Dict[str, float]:
        """
        提取结构特征
        
        Returns:
            包含结构特征的字典
        """
        # 段落数
        paragraphs = self.text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        paragraph_count = len(paragraphs)
        
        # 段落平均句数
        paragraph_sentence_counts = []
        for para in paragraphs:
            # 中文分句
            para_sentences = re.split(r'[。！？.!?]', para)
            para_sentences = [s.strip() for s in para_sentences if s.strip()]
            paragraph_sentence_counts.append(len(para_sentences))
        
        avg_sentences_per_para = statistics.mean(paragraph_sentence_counts) if paragraph_sentence_counts else 0
        
        return {
            '段落数': paragraph_count,
            '段落平均句数': round(avg_sentences_per_para, 2)
        }
    
    def extract_all_features(self) -> Dict[str, Any]:
        """
        提取所有风格特征
        
        Returns:
            包含所有特征的字典
        """
        features = {
            '句法特征': self.extract_syntax_features(),
            '词汇特征': self.extract_lexical_features(),
            '可读性特征': self.extract_readability_features(),
            '韵律特征': self.extract_rhythm_features(),
            '结构特征': self.extract_structure_features()
        }
        
        return features
    
    def get_word_frequency(self, top_n: int = 50) -> Dict[str, int]:
        """
        获取原始词频统计（不过滤，全部交给 LLM 处理）
        
        Args:
            top_n: 返回前 N 个高频词
            
        Returns:
            词频字典
        """
        # 只过滤停用词和标点，保留所有内容
        filtered_words = [
            w for w in self.words_lower 
            if w and w not in self.stop_words_cn and len(w) > 1
        ]
        
        # 统计词频，直接返回，不做任何过滤
        word_counts = Counter(filtered_words)
        return dict(word_counts.most_common(top_n))


class LLMStyleAnalyzer:
    """使用 LLM 进行文本风格分析 - 用于后续改写"""
    
    def __init__(self, model: str = "qwen-max"):
        """
        初始化 LLM 分析器
        
        Args:
            model: 模型名称
        """
        if not LLM_AVAILABLE:
            raise ImportError("langchain-community 未安装，无法使用 LLM 分析功能")
        
        self.llm = Tongyi(model=model)
        # 深度风格分析提示词 - 专业文体分析框架
        self.prompt_template = """你是一位资深的文体分析专家和文学批评家，具备敏锐的文本洞察力和深厚的理论素养。你擅长从多维角度解构文章的底层风格密码，揭示其叙事逻辑、语言美学、价值立场和文体策略。

【核心任务】
对提供的文本进行深度风格分析，系统解构其文体特征和写作范式，为后续的文本改写提供详细指导。

【分析框架】
一、叙事逻辑分析
- 时间结构：线性编年/插叙倒叙/时空交织/主题切片
- 因果关系：单因单果/多因一果/因果互构
- 叙事视角：全知/限知/多视角转换

二、语言特征分析
- 词汇谱系：文言/白话/专业术语/形容词动词密度
- 句式结构：长短句比例/复杂复句/对仗排比/主动被动
- 语体特征：庄重/平实/抒情/幽默/讽刺

三、修辞策略分析
- 比喻象征：核心意象系统/比喻类型和密度
- 评价语言：评价词强度/评价与事实结合方式
- 引用互文：直接引用/间接引用/化用典故

四、文体功能分析
- 权威建构：数据精确/文献引用/专家背书
- 合法性论证：历史必然性/现实必要性/价值正当性
- 价值引导：价值主张/呈现方式/冲突处理

五、结构形式分析
- 整体架构：章节体系/标题风格/内容分配逻辑
- 信息密度：事实与阐释比例/细节描写密度
- 视觉设计：标题层级/段落长度/图文穿插

【输出要求】
请严格按照以下 JSON 格式输出，确保内容详细、专业、有深度。**重要：请将深度分析的每个维度都转化为具体的风格标签，不要单独输出深度分析报告**。

{{
  "overall_style_summary": "150-250 字的整体风格概述，全面概括文本的风格特点、写作特色、语言风格和给人的总体印象",
  "style_labels": [
    {{
      "label": "风格标签 1（2-8 个字，精准概括，如：线性编年叙事、半文半白、典故化标题、权威建构等）",
      "score": 5,
      "guidance": "具体、可操作的改写指导，100 字左右，说明如何在改写时体现这种风格，包括具体的句式、词汇、修辞等技巧"
    }},
    {{
      "label": "风格标签 2",
      "score": 4,
      "guidance": "具体、可操作的改写指导"
    }}
    // ... 共 15-20 个风格标签，覆盖叙事逻辑、语言特征、修辞策略、文体功能、结构形式等所有维度
  ],
  "rewrite_suggestions": [
    "具体的改写建议 1，如'保持客观中立的叙述视角，避免使用第一人称'",
    "具体的改写建议 2，如'多使用复合句，通过连词连接多个分句'",
    "具体的改写建议 3，如'适当引用权威观点和数据增强说服力'",
    "具体的改写建议 4，如'使用半文半白的语言，文言词汇占比约 20%'",
    "具体的改写建议 5，如'采用线性时间叙事，构建'问题 - 努力 - 结果 - 影响'的完整因果链'"
  ]
}}

【风格标签生成指南】
请从以下维度生成风格标签（每个维度至少生成 2-3 个标签）：
1. 叙事逻辑：如"线性编年体"、"因果闭环"、"全知视角"等
2. 语言特征：如"半文半白"、"长句主导"、"庄重语体"等
3. 修辞策略：如"典故化修辞"、"辩证评价"、"多源互文"等
4. 文体功能：如"数据权威"、"三重认证"、"价值引导"等
5. 结构形式：如"三级标题"、"疏密有致"、"图文穿插"等

【待分析文本】
{text}

请直接输出 JSON 格式结果，不要包含任何其他说明文字："""
        
        # 词频过滤提示词 - 强调只保留真正的风格词
        self.word_freq_prompt = """你是一个专业的文本风格分析助手。请严格筛选以下词频列表，只保留**真正影响文章风格的词汇**。

【重要要求】
1. **必须删除**所有与具体内容相关的词（如：办学、教育、学校、医院、专业等名词）
2. **只保留**能体现写作风格的"功能词"和"修辞词"
3. **输出结果应该适用于任何文本的风格改写指导**
4. **至少保留 10-20 个风格词**，如果不够请从原文中补充

【保留标准 - 这些词能体现风格】（优先级从高到低）
- 连词/逻辑词：因为、所以、但是、然而、而且、因此、由于、乃至
- 语气助词：的、了、着、过、吗、呢、吧
- 情态动词：能、可以、应该、必须、会、将
- 程度副词：很、非常、特别、十分、最、更、极其、尤其
- 评价形容词：优秀、卓越、伟大、重要、显著（体现情感色彩）
- 四字成语：任何四字固定搭配
- 时间副词：曾经、已经、正在、即将

【删除标准 - 这些是内容词】（必须删除）
- 具体名词：学校、教育、专业、课程、学堂、医院、科室（与内容相关）
- 人名、地名、机构名
- 时间词、数字
- 动词（除了情态动词）

输入词频列表：
{word_freq}

请用 JSON 格式输出筛选后的词频：
{{
  "filtered_word_freq": {{
    "风格词 1": 频率，
    "风格词 2": 频率，
    ...（至少 10 个词）
  }},
  "explanation": "一句话说明保留了哪些类型的风格词，例如'保留了连词、程度副词、语气助词等风格词'"
}}

**注意：如果过滤后少于 10 个词，请重新检查原文，补充遗漏的风格词！**

直接输出 JSON，不要其他说明："""
    
    def analyze(self, text: str, max_length: int = 2000) -> Dict[str, Any]:
        """
        分析文本风格
        
        Args:
            text: 待分析的文本
            max_length: 最大文本长度（超过则截断）
            
        Returns:
            包含风格标签的字典
        """
        # 截断过长的文本
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # 构建提示词
        prompt = self.prompt_template.format(text=text)
        
        try:
            # 调用 LLM
            response = self.llm.invoke(prompt)
            
            # 解析 JSON 响应
            response_text = response.strip()
            
            # 尝试提取 JSON 内容
            if '```json' in response_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误：{e}")
            print(f"原始响应：{response}")
            return {'style_labels': [], 'error': 'JSON 解析失败'}
        except Exception as e:
            print(f"LLM 分析出错：{e}")
            return {'style_labels': [], 'error': str(e)}
    
    def filter_word_frequency(self, word_freq: Dict[str, int]) -> Dict[str, Any]:
        """
        使用 LLM 过滤词频，保留风格词
        
        Args:
            word_freq: 原始词频字典
            
        Returns:
            过滤后的词频结果
        """
        try:
            # 构建词频字符串
            word_freq_str = json.dumps(word_freq, ensure_ascii=False)
            
            # 构建提示词
            prompt = self.word_freq_prompt.format(word_freq=word_freq_str)
            
            # 调用 LLM
            response = self.llm.invoke(prompt)
            
            # 解析 JSON 响应
            response_text = response.strip()
            
            # 尝试提取 JSON 内容
            if '```json' in response_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"词频过滤 JSON 解析错误：{e}")
            return {'filtered_word_freq': word_freq, 'error': 'JSON 解析失败，使用原始词频'}
        except Exception as e:
            print(f"词频过滤出错：{e}")
            return {'filtered_word_freq': word_freq, 'error': str(e)}


def extract_text_from_docx(file_path: str) -> str:
    """
    从 Word 文档中提取文本
    
    Args:
        file_path: Word 文档路径
        
    Returns:
        提取的文本内容
    """
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return '\n\n'.join(paragraphs)


def save_word_cloud(word_freq: Dict[str, int], output_path: str, is_chinese: bool = True) -> str:
    """
    生成并保存词云图
    
    Args:
        word_freq: 词频字典
        output_path: 输出路径
        is_chinese: 是否为中文
        
    Returns:
        输出文件路径
    """
    if not WORDCLOUD_AVAILABLE:
        return ""
    
    try:
        # 设置字体路径（中文需要特殊字体）
        if is_chinese:
            font_path = "msyh.ttc"  # 微软雅黑
        else:
            font_path = None
        
        # 生成词云
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            colormap='viridis'
        )
        
        wc.generate_from_frequencies(word_freq)
        
        # 保存图片
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
        
    except Exception as e:
        print(f"生成词云失败：{e}")
        return ""


def analyze_document(file_path: str, use_llm: bool = False, output_dir: str = None) -> Dict[str, Any]:
    """
    分析文档并提取风格特征
    
    Args:
        file_path: Word 文档路径
        use_llm: 是否使用 LLM 分析
        output_dir: 输出目录
        
    Returns:
        包含所有风格特征的字典
    """
    # 使用默认配置
    if output_dir is None:
        output_dir = 配置['输出目录']
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 提取文本
    text = extract_text_from_docx(file_path)
    
    if not text:
        return {'error': '无法从文档中提取文本'}
    
    # 创建风格提取器并提取特征
    extractor = StyleExtractor(text)
    features = extractor.extract_all_features()
    
    # 添加基本信息（使用中文键名）
    features['基本信息'] = {
        '文件名': os.path.basename(file_path),
        '总词数': len(extractor.words),
        '总句数': len(extractor.sentences),
        '段落数': features['结构特征']['段落数']
    }
    
    # 使用 LLM 分析风格并过滤词频
    if use_llm:
        try:
            llm_analyzer = LLMStyleAnalyzer(model=配置 ['模型名称'])
            
            # 1. 分析文本风格
            llm_result = llm_analyzer.analyze(text, max_length=配置 ['句子最大长度'])
            features['LLM 风格分析'] = llm_result
            
            # 2. 获取原始词频
            word_freq = extractor.get_word_frequency(top_n=配置 ['最大词频数'])
            
            # 3. 使用 LLM 过滤词频（增加稳定性要求）
            print(f"  正在使用 LLM 过滤词频...")
            filtered_result = llm_analyzer.filter_word_frequency(word_freq)
            
            # 4. 只保留过滤后的词频
            features['词频统计'] = filtered_result.get('filtered_word_freq', {})
            features['词频说明'] = filtered_result.get('explanation', '')
            
        except Exception as e:
            features['LLM 风格分析'] = {'error': str(e)}
            # LLM 失败时仍保留原始词频
            word_freq = extractor.get_word_frequency(top_n=配置 ['最大词频数'])
            features['词频统计'] = word_freq
            features['词频说明'] = 'LLM 过滤失败，使用原始词频'
    else:
        # 不使用 LLM 时，仍保留原始词频
        word_freq = extractor.get_word_frequency(top_n=配置 ['最大词频数'])
        features['词频统计'] = word_freq
        features['词频说明'] = '未启用 LLM，使用原始词频'
    
    # 保存为 JSON 文件
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    json_path = os.path.join(output_dir, f"{base_name}_style.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(features, f, ensure_ascii=False, indent=2)
    
    features['json_path'] = json_path
    
    return features


def print_style_report(features: Dict[str, Any]) -> None:
    """
    打印风格分析报告
    
    Args:
        features: 风格特征字典
    """
    print("\n" + "="*80)
    print("文章风格分析报告")
    print("="*80)
    
    if 'error' in features:
        print(f"错误：{features['error']}")
        return
    
    # 基本信息
    basic = features.get('basic_info', {})
    print(f"\n📄 文件：{basic.get('file_name', 'N/A')}")
    print(f"📊 总词数：{basic.get('total_words', 0)}")
    print(f"📝 总句数：{basic.get('total_sentences', 0)}")
    print(f"📑 段落数：{basic.get('total_paragraphs', 0)}")
    
    # 句法特征
    print("\n" + "-"*80)
    print("🔤 句法特征")
    print("-"*80)
    syntax = features.get('syntax', {})
    print(f"  平均句长：{syntax.get('avg_sentence_length', 0):.2f} 词")
    print(f"  句长标准差：{syntax.get('sentence_length_std', 0):.2f}")
    print(f"  平均从句数：{syntax.get('avg_clause_count', 0):.2f}")
    print(f"  标点密度：{syntax.get('punctuation_density', 0):.2f} /100 词")
    
    # 词汇特征
    print("\n" + "-"*80)
    print("📚 词汇特征")
    print("-"*80)
    lexical = features.get('lexical', {})
    print(f"  词汇丰富度：{lexical.get('lexical_richness', 0):.4f}")
    print(f"  高频词占比：{lexical.get('common_word_ratio', 0):.2f}%")
    print(f"  人称代词占比：{lexical.get('pronoun_ratio', 0):.2f}%")
    print(f"  情态动词密度：{lexical.get('modal_verb_density', 0):.2f}%")
    
    pos_dist = lexical.get('pos_distribution', {})
    if pos_dist:
        print("\n  词性分布:")
        for pos, percent in sorted(pos_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {pos}: {percent:.2f}%")
    
    # 可读性特征
    print("\n" + "-"*80)
    print("📖 可读性特征")
    print("-"*80)
    readability = features.get('readability', {})
    print(f"  Flesch-Kincaid 等级：{readability.get('flesch_kincaid_grade', 0):.2f}")
    print(f"  被动语态比例：{readability.get('passive_voice_ratio', 0):.2f}%")
    print(f"  连词密度：{readability.get('conjunction_density', 0):.2f}%")
    
    # 韵律特征
    print("\n" + "-"*80)
    print("🎵 韵律特征")
    print("-"*80)
    rhythm = features.get('rhythm', {})
    print(f"  平均词长：{rhythm.get('avg_word_length', 0):.2f} 字符")
    print(f"  平均每词音节数：{rhythm.get('avg_syllables_per_word', 0):.2f}")
    
    syllable_dist = rhythm.get('syllable_distribution', {})
    if syllable_dist:
        print("\n  音节分布:")
        for syl, percent in sorted(syllable_dist.items()):
            print(f"    {syl}: {percent:.2f}%")
    
    # 结构特征
    print("\n" + "-"*80)
    print("📐 结构特征")
    print("-"*80)
    structure = features.get('structure', {})
    print(f"  段落数：{structure.get('paragraph_count', 0)}")
    print(f"  段落平均句数：{structure.get('avg_sentences_per_paragraph', 0):.2f}")
    
    # LLM 分析结果
    llm_analysis = features.get('llm_analysis', {})
    if llm_analysis and 'error' not in llm_analysis:
        print("\n" + "-"*80)
        print("🤖 LLM 风格分析")
        print("-"*80)
        style_labels = llm_analysis.get('style_labels', [])
        if style_labels:
            print("  风格标签:")
            for item in style_labels:
                label = item.get('label', 'N/A')
                score = item.get('score', 0)
                evidence = item.get('evidence', '')
                score_bar = '★' * score + '☆' * (5 - score)
                print(f"    • {label}: {score_bar} ({score}/5)")
                if evidence:
                    print(f"      依据：{evidence}")
        else:
            print("  未获取到风格标签")
    
    print("\n" + "="*80)
    print("分析完成")
    print("="*80 + "\n")


def main():
    """主函数"""
    # 使用配置项中的目录
    示例目录 = 配置['示例目录']
    输出目录 = 配置['输出目录']
    
    # 查找所有 Word 文档
    docx_files = []
    for file in os.listdir(示例目录):
        if file.endswith('.docx'):
            docx_files.append(os.path.join(示例目录, file))
    
    if not docx_files:
        print(f"在 {示例目录} 目录中没有找到 Word 文档")
        return
    
    print(f"找到 {len(docx_files)} 个 Word 文档")
    
    # 询问是否使用 LLM 分析
    if LLM_AVAILABLE:
        print(f"\n是否启用 LLM 风格分析和词频过滤？(y/n): ", end='')
        try:
            use_llm = input().strip().lower() == 'y'
        except:
            use_llm = False
    else:
        use_llm = False
    
    # 分析每个文档
    print(f"\n分析结果将保存到：{输出目录}")
    for file_path in docx_files:
        print(f"\n正在分析：{os.path.basename(file_path)}")
        try:
            features = analyze_document(file_path, use_llm=use_llm, output_dir=输出目录)
            print(f"  ✓ JSON 文件：{features.get('json_path', 'N/A')}")
        except Exception as e:
            print(f"分析 {file_path} 时出错：{str(e)}")
    
    print(f"\n所有文档分析完成！结果已保存到 {输出目录} 目录")


if __name__ == "__main__":
    main()
