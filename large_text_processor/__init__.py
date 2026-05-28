"""
超大文本处理模块
支持 PDF 和 Word 文档的分批处理、风格提取、智能改写
"""

from .document_processor import DocumentProcessor
from .style_extractor_batch import BatchStyleExtractor
from .style_index import StyleIndex
from .rewrite_agent import RewriteAgent
from .quality_checker import QualityChecker

__all__ = [
    'DocumentProcessor',
    'BatchStyleExtractor',
    'StyleIndex',
    'RewriteAgent',
    'QualityChecker'
]
