"""
文章风格改写器
将目标文章改写成与示例风格相似的文本
"""

import re
import json
from typing import Dict, List, Any

# 尝试导入 LLM 相关库
try:
    from langchain_community.llms.tongyi import Tongyi
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告：langchain-community 未安装，无法使用改写功能")


class StyleRewriter:
    """文章风格改写器"""
    
    def __init__(self, model: str = "qwen-max"):
        """
        初始化改写器
        
        Args:
            model: 模型名称
        """
        if not LLM_AVAILABLE:
            raise ImportError("langchain-community 未安装，无法使用改写功能")
        
        self.llm = Tongyi(model=model)
        
        # 文章改写提示词 - 核心提示词
        self.rewrite_prompt = """你是一位专业的文本改写专家，擅长将一篇文章改写成另一种风格。

【任务描述】
你将收到：
1. 一篇**目标文章**（需要被改写的原文）
2. 一组**风格标签**（定义了目标风格的特征）
3. **风格词频**（目标风格偏好的词汇）
4. **量化风格特征**（句法、词汇、可读性等具体数值）

你的任务是将目标文章完全改写成符合这些风格特征的文本，保持原文的核心信息和逻辑，但改变表达方式、语言风格、句式结构等。

【改写要求】

## 核心原则
1. **忠于原意**：保持原文的核心事实、数据、观点不变
2. **风格转换**：全面应用风格标签中的改写指导
3. **自然流畅**：改写后的文本要自然、连贯、可读
4. **长度相当**：改写后的文本长度应与原文相当（±20%）

## 小标题风格改写（重要）

原文中如果有小标题，需要根据风格标签调整小标题的风格：

### 小标题改写策略
- **典故化标题**：如"白鹿开先"、"杏岭肇基"、"筚路蓝缕"
- **事实陈述式**：如"第一章 学校创立"、"第二节 发展历程"
- **问题导向式**：如"如何解决师资短缺？"、"为什么选择这个方案？"
- **文学化表达**：如"春风化雨润物无声"、"薪火相传弦歌不辍"
- **简洁数字式**：如"一、背景"、"二、方法"、"三、成果"

### 小标题改写示例
- 原文："1. 学校创立背景" → 改写："一、肇基立业：时代呼唤新教育"
- 原文："2. 发展历程" → 改写："二、筚路蓝缕：艰苦创业之路"
- 原文："3. 取得的成就" → 改写："三、桃李芬芳：辉煌成就展示"

## 风格应用策略

### 1. 应用风格标签（最重要）
请逐条阅读风格标签，并在改写时有意识地应用：
- 对于每个风格标签，思考"如何在改写中体现这种风格？"
- 将风格指导转化为具体的写作行为
- 例如：
  - "线性编年叙事" → 按时间顺序组织内容，使用"首先...然后...最后"等时间连接词
  - "半文半白" → 适当使用文言词汇（约 20%），如"乃"、"遂"、"盖"等
  - "权威建构" → 引用数据、文献、专家观点增强可信度
  - "长句主导" → 多使用 15-25 字的长句，通过连词连接多个分句
  - "典故化修辞" → 适当使用典故、成语、历史类比

### 2. 参考量化特征（重要）
根据提供的量化特征调整写作：
- **句法特征**：
  - 平均句长 → 调整句子长度（如平均句长 20 字，则多数句子控制在 18-22 字）
  - 句长标准差 → 控制句子长度的变化（标准差大则长短句交替，小则保持均匀）
  - 标点密度 → 调整标点使用频率
- **词汇特征**：
  - 词汇丰富度 → 控制词汇多样性（高则多用同义词替换，低则重复使用核心词）
  - 高频词占比 → 适当重复使用某些关键词
- **可读性特征**：
  - Flesch-Kincaid 等级 → 调整文本难度（等级高则用复杂句和专业术语，低则用简单句和日常词汇）

### 3. 应用风格词频
- 参考"风格词频"中的词汇，在改写中有意识地使用这些词
- 但不要生硬插入，要自然融入文本

## 句式调整
根据风格标签和量化特征，调整：
- 句长（长句/短句）
- 句型（陈述句/疑问句/感叹句）
- 语态（主动/被动）
- 语气（正式/非正式/庄重/轻松）

## 段落重组
根据风格标签的指导：
- 调整段落长度
- 改变段落开头方式（如以设问句开头）
- 增加/减少过渡段

【输出格式】
请直接输出改写后的完整文章，不要包含任何说明文字、注释或标记。**保留原文的标题层级结构**（如一级标题、二级标题、三级标题），但要根据风格标签调整标题的表达方式。

【目标文章】
{target_text}

【风格标签】
{style_labels}

【风格词频（参考）】
{style_words}

【量化特征（参考）】
{quantitative_features}

【改写后的文章】"""
    
    def rewrite(self, 
                target_text: str, 
                style_labels: List[Dict[str, Any]], 
                style_words: Dict[str, int] = None,
                quantitative_features: Dict[str, Any] = None,
                max_length: int = 5000) -> str:
        """
        改写文章
        
        Args:
            target_text: 目标文章（需要被改写的原文）
            style_labels: 风格标签列表（来自 LLM 分析）
            style_words: 风格词频字典（可选）
            quantitative_features: 量化特征字典（可选，包含句法、词汇、可读性等特征）
            max_length: 最大文本长度
            
        Returns:
            改写后的文章
        """
        # 截断过长的文本
        if len(target_text) > max_length:
            target_text = target_text[:max_length] + "..."
        
        # 格式化风格标签
        style_labels_str = self._format_style_labels(style_labels)
        
        # 格式化风格词频
        style_words_str = self._format_style_words(style_words) if style_words else "暂无"
        
        # 格式化量化特征
        quantitative_features_str = self._format_quantitative_features(quantitative_features) if quantitative_features else "暂无"
        
        # 构建提示词
        prompt = self.rewrite_prompt.format(
            target_text=target_text,
            style_labels=style_labels_str,
            style_words=style_words_str,
            quantitative_features=quantitative_features_str
        )
        
        try:
            # 调用 LLM
            response = self.llm.invoke(prompt)
            
            # 清理响应文本
            rewritten_text = response.strip()
            
            # 移除可能的 markdown 标记
            if rewritten_text.startswith('```'):
                rewritten_text = re.sub(r'^```.*?\n', '', rewritten_text)
                rewritten_text = re.sub(r'\n```$', '', rewritten_text)
            
            return rewritten_text
            
        except Exception as e:
            print(f"改写失败：{e}")
            return f"[改写失败：{str(e)}]"
    
    def _format_style_labels(self, style_labels: List[Dict[str, Any]]) -> str:
        """格式化风格标签为易读的文本"""
        formatted = []
        for i, label in enumerate(style_labels, 1):
            label_text = label.get('label', '未知')
            score = label.get('score', 0)
            guidance = label.get('guidance', '')
            
            stars = '⭐' * score + '☆' * (5 - score)
            formatted.append(f"{i}. {label_text} {stars}")
            if guidance:
                formatted.append(f"   指导：{guidance}")
        
        return '\n'.join(formatted)
    
    def _format_style_words(self, style_words: Dict[str, int]) -> str:
        """格式化风格词频为易读的文本"""
        # 取前 30 个高频词
        top_words = sorted(style_words.items(), key=lambda x: x[1], reverse=True)[:30]
        return ', '.join([f"{word}({count})" for word, count in top_words])
    
    def _format_quantitative_features(self, features: Dict[str, Any]) -> str:
        """格式化量化特征为易读的文本"""
        formatted = []
        
        # 句法特征
        if '句法特征' in features:
            syntax = features['句法特征']
            formatted.append("【句法特征】")
            formatted.append(f"- 平均句长：{syntax.get('平均句长', 0):.1f} 字")
            formatted.append(f"- 句长标准差：{syntax.get('句长标准差', 0):.2f}")
            formatted.append(f"- 标点密度：{syntax.get('标点密度', 0):.2f}")
        
        # 词汇特征
        if '词汇特征' in features:
            lexical = features['词汇特征']
            formatted.append("\n【词汇特征】")
            formatted.append(f"- 词汇丰富度：{lexical.get('词汇丰富度', 0):.4f}")
            formatted.append(f"- 高频词占比：{lexical.get('高频词占比', 0):.2f}%")
        
        # 可读性特征
        if '可读性特征' in features:
            readability = features['可读性特征']
            formatted.append("\n【可读性特征】")
            formatted.append(f"- Flesch-Kincaid 等级：{readability.get('Flesch-Kincaid 等级', 0):.1f}")
            formatted.append(f"- 被动语态比例：{readability.get('被动语态比例', 0):.2f}%")
        
        return '\n'.join(formatted) if formatted else "暂无量化特征"
    
    def rewrite_with_comparison(self, 
                                 target_text: str, 
                                 style_labels: List[Dict[str, Any]], 
                                 style_words: Dict[str, int] = None,
                                 quantitative_features: Dict[str, Any] = None) -> Dict[str, str]:
        """
        改写文章并返回对比结果
        
        Args:
            target_text: 目标文章
            style_labels: 风格标签列表
            style_words: 风格词频字典
            quantitative_features: 量化特征字典
            
        Returns:
            包含原文、改写文和统计信息的字典
        """
        rewritten_text = self.rewrite(target_text, style_labels, style_words, quantitative_features)
        
        return {
            'original': target_text,
            'rewritten': rewritten_text,
            'original_length': len(target_text),
            'rewritten_length': len(rewritten_text),
            'length_ratio': len(rewritten_text) / len(target_text) if target_text else 0
        }


def main():
    """测试改写功能"""
    if not LLM_AVAILABLE:
        print("LLM 不可用，无法测试")
        return
    
    # 示例测试
    target_text = """江西大学创立于 1940 年，是江西省第一所现代高等学府。学校初创时期条件艰苦，但在一批爱国教育家的努力下，逐渐发展壮大。"""
    
    style_labels = [
        {
            'label': '线性编年叙事',
            'score': 5,
            'guidance': '按时间顺序组织内容，使用"首先...然后...最后"等时间连接词，构建清晰的历史脉络'
        },
        {
            'label': '半文半白',
            'score': 4,
            'guidance': '适当使用文言词汇（约 20%），如"乃"、"遂"、"盖"、"初"等，形成典雅与通俗的平衡'
        },
        {
            'label': '权威建构',
            'score': 5,
            'guidance': '引用具体数据、文献、专家观点增强可信度，如"据记载"、"据统计"等'
        },
        {
            'label': '长句主导',
            'score': 3,
            'guidance': '多使用 15-25 字的长句，通过连词连接多个分句，增加信息密度'
        }
    ]
    
    style_words = {
        '创立': 5,
        '发展': 4,
        '逐渐': 3,
        '乃': 2,
        '遂': 2,
        '据记载': 2
    }
    
    rewriter = StyleRewriter()
    result = rewriter.rewrite_with_comparison(target_text, style_labels, style_words)
    
    print("=" * 80)
    print("原文：")
    print(result['original'])
    print(f"\n原文长度：{result['original_length']} 字")
    print("=" * 80)
    print("改写后：")
    print(result['rewritten'])
    print(f"\n改写后长度：{result['rewritten_length']} 字")
    print(f"长度比例：{result['length_ratio']:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
