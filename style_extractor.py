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
    '示例目录': os.path.join(os.path.dirname(__file__), 'data', 'example'),
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
    """使用 LLM 进行文本风格分析 - 用于后续改写（支持自动切换模型和 Ollama 本地模型）"""
    
    # 可用模型列表（按优先级排序）
    AVAILABLE_MODELS = [
        # DeepSeek API（推荐）
        'deepseek-api:deepseek-v4-flash',  # DeepSeek V4 Flash，速度快效果好
        'deepseek-api:deepseek-v4-pro',    # DeepSeek V4 Pro，效果更好
    ]
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    
    # Ollama 服务器地址
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # Ollama 超时时间（秒）- 本地模型可能较慢，设置20分钟
    OLLAMA_TIMEOUT = 1200
    
    def __init__(self, model: str = "deepseek-api:deepseek-v4-flash", auto_switch: bool = True, deepseek_api_key: str = ''):
        """
        初始化 LLM 分析器
        
        Args:
            model: 模型名称
            auto_switch: 是否在出错时自动切换模型
            deepseek_api_key: DeepSeek API Key（前端传入，优先使用）
        """
        self.model = model
        self.auto_switch = auto_switch
        self.current_model_index = self._get_model_index(model)
        
        # DeepSeek API Key（优先使用前端传入的）
        self._deepseek_api_key = deepseek_api_key or os.environ.get('DEEPSEEK_API_KEY', '')
        
        # 缓存 Ollama 服务状态，避免每次调用都检查
        self._ollama_checked = False
        self._ollama_available_models = []
        
        # 多维度开放标签风格分析提示词
        self.prompt_template = """分析以下文本的风格特征，输出 JSON 格式结果。

【分析要求】
1. 从以下维度逐一分析文本的风格特征（每个维度可列出 1~3 个最显著的标签，每个标签给出 1-5 分并附上文本依据）：
   - 词汇风格：例如：口语化/书面化、古语词/现代词、抽象/具体、华丽/朴实、术语密度、叠词使用等。
   - 句法风格：例如：长句/短句、并列/复合句、倒装/省略、重复结构、标点特色（如破折号、省略号）等。
   - 修辞风格：例如：比喻、拟人、排比、反问、夸张、双关、对偶、反讽、借代、通感等。
   - 语气与情感：例如：幽默、严肃、讽刺、感伤、激昂、平静、亲切、冷漠、客观、主观等。
   - 语体与正式度：例如：公文/学术/新闻/广告/小说/日记/社交媒体，正式/半正式/非正式。
   - 时代感与文化风格：例如：古风、现代、未来感、地域特色（如京味、东北话）、网络流行语等。
   - 叙事风格（若适用）：例如：第一人称/第三人称、主观/客观、线性/跳跃、全知/限知视角等。

2. 如果文本还有其他上述维度未覆盖的重要风格特征（如节奏快慢、画面感强、对话性强、逻辑严密、情感充沛等），请自行在"其他显著风格"字段中补充。

3. 最后用一段话（150-250 字）总结该文本的整体风格，语言要具体、可操作，能够直接用于后续改写指导。

【重要原则】
- 标签要灵活：不要局限于示例标签，根据文本实际情况选择最合适的描述词
- 证据要充分：每个标签必须提供文本中的具体片段作为依据
- 评分要准确：1 分=不明显，3 分=中等，5 分=非常显著
- 避免套话：不要使用"半文半白"这类万能标签，要精准描述文本的真实特征

【JSON格式要求】
1. 每个维度后面必须有逗号
2. 数组元素之间必须有逗号
3. 空数组写 []
4. 不要输出任何其他内容

【输出模板】
{{
  "dimensions": {{
    "词汇风格": [{{"label": "标签", "score": 3, "evidence": "文本依据"}}],
    "句法风格": [{{"label": "标签", "score": 3, "evidence": "文本依据"}}],
    "修辞风格": [],
    "语气与情感": [{{"label": "标签", "score": 3, "evidence": "文本依据"}}],
    "语体与正式度": [{{"label": "标签", "score": 3, "evidence": "文本依据"}}],
    "时代感与文化风格": [],
    "叙事风格": []
  }},
  "other_styles": [],
  "summary": "整体风格描述（50字以内）"
}}

【待分析文本】
{text}

JSON："""
    
    def _get_model_index(self, model: str) -> int:
        """获取模型在列表中的索引"""
        if model in self.AVAILABLE_MODELS:
            return self.AVAILABLE_MODELS.index(model)
        return 0
    
    def _call_llm(self, prompt: str, model: str) -> str:
        """调用 LLM API"""
        # 检查是否是 DeepSeek API 模型
        if model.startswith('deepseek-api:'):
            return self._call_deepseek_api(prompt, model.replace('deepseek-api:', ''))
        
        # 检查是否是 Ollama 模型
        if model.startswith('ollama:'):
            return self._call_ollama(prompt, model.replace('ollama:', ''))
        
        # 阿里云百练模型
        import dashscope
        from dashscope import Generation
        
        try:
            # 尝试使用 Generation API
            response = Generation.call(
                model=model,
                prompt=prompt,
                max_tokens=2000
            )
            
            if response.status_code == 200:
                # 尝试不同的返回格式
                if hasattr(response.output, 'text') and response.output.text:
                    return response.output.text
                elif hasattr(response.output, 'choices') and response.output.choices:
                    choice = response.output.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        return choice.message.content
                    elif hasattr(choice, 'text'):
                        return choice.text
                else:
                    print(f"未知的返回格式: {dir(response.output)}")
                    return None
            else:
                raise Exception(f"API 调用失败: {response.code} - {response.message}")
        except Exception as e:
            error_msg = str(e)
            # 如果是 url error，尝试使用 ChatCompletion API
            if 'url error' in error_msg.lower() or 'InvalidParameter' in error_msg:
                print(f"Generation API 不支持模型 {model}，尝试 ChatCompletion API...")
                return self._call_llm_chat(prompt, model)
            raise Exception(f"模型 {model} 调用异常: {error_msg}")
    
    def _call_deepseek_api(self, prompt: str, model: str) -> str:
        """调用 DeepSeek API（OpenAI 兼容格式）"""
        import requests
        import json
        
        # 获取 API Key（优先使用前端传入的）
        api_key = self._deepseek_api_key
        if not api_key:
            raise Exception("DeepSeek API Key 未设置，请在页面中填写 API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        try:
            print(f"正在调用 DeepSeek API ({model})...")
            
            response = requests.post(
                f"{self.DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                timeout=300  # 5分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                if content:
                    print(f"DeepSeek API 调用成功，返回 {len(content)} 字符")
                    return content
                else:
                    raise Exception("DeepSeek API 返回内容为空")
            else:
                error_detail = response.text[:500] if response.text else "无详细信息"
                raise Exception(f"DeepSeek API 调用失败: {response.status_code} - {error_detail}")
                
        except requests.exceptions.Timeout:
            raise Exception("DeepSeek API 调用超时（超过 300 秒）")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"DeepSeek API 连接失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"DeepSeek API 返回格式错误: {str(e)}")
        except Exception as e:
            error_msg = str(e)
            if 'DeepSeek' not in error_msg:
                error_msg = f"DeepSeek API 调用异常: {error_msg}"
            raise Exception(error_msg)
    
    def _call_ollama(self, prompt: str, model: str) -> str:
        """调用 Ollama 本地模型"""
        import requests
        import json
        
        try:
            # 只在第一次调用时检查 Ollama 服务状态
            if not self._ollama_checked:
                print(f"正在检查 Ollama 服务状态...")
                try:
                    response = requests.get(f"{self.OLLAMA_BASE_URL}/api/tags", timeout=30)
                    if response.status_code != 200:
                        raise Exception(f"Ollama 服务返回错误: {response.status_code}")
                    
                    # 缓存可用模型列表
                    available_models = response.json().get('models', [])
                    self._ollama_available_models = [m.get('name', '') for m in available_models]
                    print(f"Ollama 可用模型: {self._ollama_available_models}")
                    self._ollama_checked = True
                    
                except requests.exceptions.ConnectionError:
                    raise Exception(f"无法连接到 Ollama 服务 ({self.OLLAMA_BASE_URL})，请确保 Ollama 已启动\n启动方法: 在终端运行 'ollama serve'")
                except requests.exceptions.Timeout:
                    raise Exception("连接 Ollama 服务超时，请检查 Ollama 是否正常运行")
            
            # 检查模型是否可用
            if model not in self._ollama_available_models and f"{model}:latest" not in self._ollama_available_models:
                print(f"警告: 模型 {model} 未在 Ollama 中找到")
                print(f"请运行: ollama pull {model}")
                raise Exception(f"模型 {model} 未安装，请先运行: ollama pull {model}")
            
            print(f"正在调用 Ollama 模型 {model}...")
            
            # 调用 Ollama API
            response = requests.post(
                f"{self.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 4096,  # 增加到 4096，避免输出被截断
                        "temperature": 0.7
                    }
                },
                timeout=self.OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                if response_text and response_text.strip():
                    print(f"Ollama 模型 {model} 调用成功，返回 {len(response_text)} 字符")
                    return response_text
                else:
                    raise Exception("Ollama 返回内容为空")
            else:
                error_detail = response.text[:500] if response.text else "无详细信息"
                raise Exception(f"Ollama API 调用失败: {response.status_code} - {error_detail}")
                
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama 模型 {model} 调用超时（超过 {self.OLLAMA_TIMEOUT} 秒）\n建议: 尝试使用更小的模型或增加超时时间")
        except requests.exceptions.ConnectionError as e:
            # 连接失败时重置检查状态，下次调用会重新检查服务
            self._ollama_checked = False
            raise Exception(f"Ollama 连接中断: {str(e)}\n请检查 Ollama 服务是否仍在运行（可能电脑休眠后服务已停止）")
        except json.JSONDecodeError as e:
            raise Exception(f"Ollama 返回格式错误: {str(e)}")
        except Exception as e:
            error_msg = str(e)
            if 'Ollama' not in error_msg and 'ollama' not in error_msg.lower() and '模型' not in error_msg:
                error_msg = f"Ollama 调用异常: {error_msg}"
            raise Exception(error_msg)
    
    def _call_llm_chat(self, prompt: str, model: str) -> str:
        """使用 ChatCompletion API 调用 LLM"""
        import dashscope
        from http import HTTPStatus
        
        try:
            response = dashscope.Generation.call(
                model=model,
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"ChatCompletion API 调用失败: {response.code} - {response.message}")
        except Exception as e:
            raise Exception(f"ChatCompletion API 调用异常: {str(e)}")
    
    def _try_fix_json_format(self, json_text: str) -> dict:
        """
        尝试修复常见的 JSON 格式问题
        返回修复后的 dict，如果无法修复则返回 None
        """
        import re
        
        try:
            print("尝试修复 JSON 格式...")
            
            # 问题1: 键名大小写问题 - 将常见的键名转为小写
            json_text = re.sub(r'"Dimensions"', '"dimensions"', json_text, flags=re.IGNORECASE)
            json_text = re.sub(r'"Score"', '"score"', json_text, flags=re.IGNORECASE)
            json_text = re.sub(r'"Evidence"', '"evidence"', json_text, flags=re.IGNORECASE)
            json_text = re.sub(r'"Label"', '"label"', json_text, flags=re.IGNORECASE)
            
            # 问题2: 修复 "evidence": "value1", "value2", "value3" 格式
            # 这不是合法JSON，需要将多个值合并
            # 例如: "evidence": "肇基之艰", "办学宗旨", "创办" -> "evidence": "肇基之艰, 办学宗旨, 创办"
            
            # 找到所有 "key": "value", "value2", "value3" 模式
            def fix_multi_values(text):
                # 匹配 "key": 后面跟着多个用逗号分隔的字符串
                pattern = r'"(evidence|label)"\s*:\s*"([^"]+)"((?:\s*,\s*"[^"]+")+)'
                
                def replace_func(match):
                    key = match.group(1)
                    first_value = match.group(2)
                    rest_values = match.group(3)
                    # 提取剩余的值
                    rest_values = re.findall(r'"([^"]+)"', rest_values)
                    all_values = [first_value] + rest_values
                    combined = ", ".join(all_values)
                    return f'"{key}": "{combined}"'
                
                return re.sub(pattern, replace_func, text)
            
            json_text = fix_multi_values(json_text)
            
            # 问题3: 维度值应该是数组但变成了对象
            # 先尝试解析
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError:
                # 如果还是失败，尝试更激进的修复
                print("标准解析失败，尝试激进修复...")
                result = self._aggressive_json_fix(json_text)
                if result is None:
                    return None
            
            # 检查并修复维度格式
            if 'dimensions' in result or 'Dimensions' in result:
                dims = result.get('dimensions') or result.get('Dimensions', {})
                fixed_dims = {}
                
                for dim_name, dim_value in dims.items():
                    if isinstance(dim_value, dict):
                        # 需要转换为数组格式
                        score = dim_value.get('score') or dim_value.get('Score', 3)
                        evidence = dim_value.get('evidence') or dim_value.get('Evidence', '')
                        label = dim_value.get('label') or dim_value.get('Label', dim_name)
                        
                        fixed_dims[dim_name] = [{
                            'label': label,
                            'score': score,
                            'evidence': str(evidence)
                        }]
                    elif isinstance(dim_value, list):
                        fixed_dims[dim_name] = dim_value
                    else:
                        fixed_dims[dim_name] = [{
                            'label': dim_name,
                            'score': 3,
                            'evidence': str(dim_value)
                        }]
                
                result['dimensions'] = fixed_dims
            
            # 确保 summary 存在
            if 'summary' not in result:
                result['summary'] = ''
            
            print("JSON 格式修复成功")
            return result
            
        except Exception as e:
            print(f"JSON 格式修复失败: {e}")
            return None
    
    def _aggressive_json_fix(self, json_text: str) -> dict:
        """
        激进的 JSON 修复，用于处理严重格式错误
        """
        import re
        
        try:
            # 尝试提取关键信息并重建 JSON
            result = {
                'dimensions': {},
                'other_styles': [],
                'summary': ''
            }
            
            # 提取各个维度的信息
            dimension_names = ['词汇风格', '句法风格', '修辞风格', '语气与情感', '语体与正式度', '时代感与文化风格', '叙事风格']
            
            for dim_name in dimension_names:
                # 尝试找到该维度的内容 - 使用普通字符串避免 f-string 转义问题
                pattern = '"' + dim_name + r'"\s*:\s*\{([^}]+)\}'
                match = re.search(pattern, json_text)
                if match:
                    content = match.group(1)
                    # 提取 score
                    score_match = re.search(r'"score"\s*:\s*(\d+)', content, re.IGNORECASE)
                    score = int(score_match.group(1)) if score_match else 3
                    # 提取 evidence
                    evidence_match = re.search(r'"evidence"\s*:\s*"([^"]+)"', content, re.IGNORECASE)
                    evidence = evidence_match.group(1) if evidence_match else ''
                    
                    result['dimensions'][dim_name] = [{
                        'label': dim_name,
                        'score': score,
                        'evidence': evidence
                    }]
            
            if result['dimensions']:
                print("激进修复成功，提取到部分维度信息")
                return result
            else:
                return None
                
        except Exception as e:
            print(f"激进修复失败: {e}")
            return None
    
    def _call_with_auto_switch(self, prompt: str) -> str:
        """带自动切换的 LLM 调用"""
        errors = []
        
        for i in range(self.current_model_index, len(self.AVAILABLE_MODELS)):
            model = self.AVAILABLE_MODELS[i]
            try:
                print(f"尝试使用模型: {model}")
                result = self._call_llm(prompt, model)
                
                # 检查返回值是否有效
                if result and result.strip():
                    self.model = model  # 更新当前成功的模型
                    self.current_model_index = i
                    return result
                else:
                    error_msg = "返回内容为空"
                    errors.append(f"{model}: {error_msg}")
                    print(f"模型 {model} 返回为空，切换到下一个模型...")
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{model}: {error_msg}")
                print(f"模型 {model} 调用失败: {error_msg}")
                
                # 判断是否需要切换到下一个模型
                should_switch = (
                    'quota' in error_msg.lower() or 
                    'limit' in error_msg.lower() or 
                    '400' in error_msg or 
                    'InvalidParameter' in error_msg or 
                    'url error' in error_msg or
                    '连接中断' in error_msg or
                    '无法连接' in error_msg or
                    '未安装' in error_msg or
                    '返回内容为空' in error_msg
                )
                
                if should_switch:
                    print(f"切换到下一个模型...")
                    continue
                else:
                    # 其他错误也尝试下一个模型
                    continue
        
        # 所有模型都失败
        raise Exception(f"所有模型都调用失败:\n" + "\n".join(errors))
        
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
            包含风格标签的字典（转换为旧格式以兼容前端）
        """
        # 截断过长的文本
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # 构建提示词
        prompt = self.prompt_template.format(text=text)
        
        try:
            # 调用 LLM（带自动切换）
            if self.auto_switch:
                response_text = self._call_with_auto_switch(prompt)
            else:
                response_text = self._call_llm(prompt, self.model)
            
            # 检查返回值
            if not response_text:
                print("LLM 返回为空")
                return {'style_labels': [], 'error': 'LLM 返回为空'}
            
            # 解析 JSON 响应
            response_text = response_text.strip()
            
            # 尝试提取 JSON 内容 - 多种格式兼容
            json_text = response_text
            
            # 格式1: ```json ... ```
            if '```json' in response_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1).strip()
            
            # 格式2: ``` ... ``` (没有json标记)
            elif '```' in response_text:
                json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1).strip()
            
            # 格式3: 查找 { ... } 的JSON对象
            if not json_text.startswith('{'):
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0).strip()
            
            # 格式4: 移除可能的前缀文本
            if '{' in json_text and not json_text.startswith('{'):
                start_idx = json_text.find('{')
                json_text = json_text[start_idx:]
            
            # 格式5: 移除尾随逗号（Python json 不支持）
            # 处理 ,] 和 ,} 的情况
            json_text = re.sub(r',(\s*[\]\}])', r'\1', json_text)
            
            # 格式5.1: 替换中文引号为单引号（模型经常在evidence中使用中文引号）
            # 注意：只替换中文引号 U+201C 和 U+201D，不要替换英文双引号
            json_text = json_text.replace('\u201c', "'").replace('\u201d', "'")  # 中文双引号 ""
            json_text = json_text.replace('\u2018', "'").replace('\u2019', "'")  # 中文单引号 ''
            
            # 格式5.5: 修复缺少逗号的问题
            # 在 } { 之间添加逗号（数组元素之间缺少逗号）
            json_text = re.sub(r'\}\s*\{', '}, {', json_text)
            # 在 ] { 之间添加逗号（对象属性之间缺少逗号）
            json_text = re.sub(r'\]\s*\{', '], {', json_text)
            # 在 } " 之间添加逗号（属性之间缺少逗号）
            json_text = re.sub(r'\}\s*"', '}, "', json_text)
            
            # 格式6: 尝试修复被截断的 JSON
            # 检查括号是否匹配
            open_braces = json_text.count('{') - json_text.count('}')
            open_brackets = json_text.count('[') - json_text.count(']')
            
            if open_braces > 0 or open_brackets > 0:
                print(f"警告: JSON 可能被截断，缺少 {open_braces} 个 }} 和 {open_brackets} 个 ]")
                # 尝试补全缺失的括号
                json_text += ']' * open_brackets + '}' * open_braces
                print(f"已尝试自动补全括号")
            
            # 尝试解析 JSON
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"JSON 解析失败，尝试修复格式错误...")
                print(f"错误详情: {e}")
                # 先打印 JSON 的前200个字符看看
                print(f"JSON前200字符: {json_text[:200]}")
                # 尝试修复常见的格式问题
                result = self._try_fix_json_format(json_text)
                if result is None:
                    raise e
            
            # 将新的维度格式转换为前端需要的旧格式
            converted_result = {
                'overall_style_summary': result.get('summary', ''),
                'style_labels': [],
                'rewrite_suggestions': []
            }
            
            # 从各个维度提取风格标签
            dimensions = result.get('dimensions', {})
            for dim_name, dim_labels in dimensions.items():
                if isinstance(dim_labels, list):
                    for label_item in dim_labels:
                        if isinstance(label_item, dict) and 'label' in label_item:
                            # 将维度信息融入到标签中
                            converted_result['style_labels'].append({
                                'label': f"{dim_name}: {label_item['label']}",
                                'score': label_item.get('score', 3),
                                'guidance': f"依据：{label_item.get('evidence', '')}"
                            })
            
            # 添加其他显著风格
            other_styles = result.get('other_styles', [])
            if isinstance(other_styles, list):
                for label_item in other_styles:
                    if isinstance(label_item, dict) and 'label' in label_item:
                        converted_result['style_labels'].append({
                            'label': f"其他：{label_item['label']}",
                            'score': label_item.get('score', 3),
                            'guidance': f"依据：{label_item.get('evidence', '')}"
                        })
            
            # 基于 summary 生成改写建议
            summary = result.get('summary', '')
            if summary:
                converted_result['rewrite_suggestions'] = [
                    f"整体风格：{summary}",
                    "请根据上述风格特征进行改写，保持原文的核心信息和逻辑结构"
                ]
            
            return converted_result
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误：{e}")
            print(f"原始响应（前500字符）：{response_text[:500] if response_text else 'None'}")
            return {'style_labels': [], 'error': 'JSON 解析失败', 'raw_response': response_text[:500] if response_text else None}
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
            
            # 调用 LLM（带自动切换）
            if self.auto_switch:
                response = self._call_with_auto_switch(prompt)
            else:
                response = self._call_llm(prompt, self.model)
            
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


def analyze_document(file_path: str, use_llm: bool = False, output_dir: str = None, model: str = None) -> Dict[str, Any]:
    """
    分析文档并提取风格特征
    
    Args:
        file_path: Word 文档路径
        use_llm: 是否使用 LLM 分析
        output_dir: 输出目录
        model: 使用的模型名称（可选，默认使用配置中的模型）
        
    Returns:
        包含所有风格特征的字典
    """
    # 使用配置项中的目录
    if output_dir is None:
        output_dir = 配置 ['输出目录']
    
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
            # 检查 API Key 是否设置
            api_key = os.environ.get('DASHSCOPE_API_KEY')
            if not api_key:
                raise Exception("未设置 DASHSCOPE_API_KEY 环境变量，请检查 Railway 环境变量配置")
            
            # 使用传入的模型或默认模型
            model_name = model if model else 配置 ['模型名称']
            llm_analyzer = LLMStyleAnalyzer(model=model_name)
            
            # 1. 分析文本风格
            print(f"  正在调用 LLM 进行风格分析（模型：{model_name}）...")
            llm_result = llm_analyzer.analyze(text, max_length=配置 ['句子最大长度'])
            
            # 检查 LLM 分析是否成功
            if 'error' in llm_result:
                raise Exception(f"LLM 分析失败：{llm_result.get('error', '未知错误')}")
            
            features['LLM 风格分析'] = llm_result
            print(f"  ✓ LLM 风格分析完成，获取到 {len(llm_result.get('style_labels', []))} 个风格标签")
            
            # 2. 获取原始词频
            word_freq = extractor.get_word_frequency(top_n=配置 ['最大词频数'])
            
            # 3. 使用 LLM 过滤词频（增加稳定性要求）
            print(f"  正在使用 LLM 过滤词频...")
            filtered_result = llm_analyzer.filter_word_frequency(word_freq)
            
            # 4. 只保留过滤后的词频
            features['词频统计'] = filtered_result.get('filtered_word_freq', {})
            features['词频说明'] = filtered_result.get('explanation', '')
            print(f"  ✓ 词频过滤完成")
            
        except ImportError as e:
            error_msg = f"LLM 库未安装：{str(e)}"
            print(f"  ✗ {error_msg}")
            features['LLM 风格分析'] = {'error': error_msg}
            features['词频统计'] = {}
            features['词频说明'] = 'LLM 不可用'
        except Exception as e:
            error_msg = f"LLM 分析出错：{str(e)}"
            print(f"  ✗ {error_msg}")
            features['LLM 风格分析'] = {'error': error_msg}
            # LLM 失败时仍保留原始词频
            word_freq = extractor.get_word_frequency(top_n=配置 ['最大词频数'])
            features['词频统计'] = word_freq
            features['词频说明'] = 'LLM 失败，使用原始词频'
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
