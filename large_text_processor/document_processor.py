"""
文档处理器 - 支持 PDF 和 Word 文档的切分和预处理
"""
import os

# 修复 PaddlePaddle 3.x oneDNN 兼容性问题（必须在导入 paddle 之前设置）
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_onednn_backend'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_pir_apply_inplace_pass'] = '0'

import re
import json
import base64
from typing import List, Dict, Any, Optional
from docx import Document
import sys

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("警告：PyPDF2 未安装，PDF 支持不可用。请运行：pip install PyPDF2")

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_SUPPORT = True
except ImportError:
    PDF2IMAGE_SUPPORT = False
    print("提示：pdf2image 未安装，扫描版 PDF OCR 功能不可用。请运行：pip install pdf2image")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_SUPPORT = True
except ImportError:
    PADDLEOCR_SUPPORT = False
    print("提示：PaddleOCR 未安装，本地 OCR 功能不可用。请运行：pip install paddlepaddle paddleocr")

try:
    import dashscope
    from dashscope import MultiModalConversation
    DASHSCOPE_SUPPORT = True
except ImportError:
    DASHSCOPE_SUPPORT = False
    print("提示：dashscope 未安装，视觉模型 OCR 功能不可用。请运行：pip install dashscope")


class DocumentProcessor:
    """文档处理器 - 切分和预处理"""
    
    def __init__(self, min_fragment_length=500, max_fragment_length=1000, use_ocr=False, ocr_engine='paddleocr'):
        """
        初始化文档处理器
        
        Args:
            min_fragment_length: 最小片段长度（字符数）
            max_fragment_length: 最大片段长度（字符数）
            use_ocr: 是否使用 OCR 处理扫描版 PDF
            ocr_engine: OCR 引擎 ('paddleocr' 或 'qwen-vl')
        """
        self.min_fragment_length = min_fragment_length
        self.max_fragment_length = max_fragment_length
        self.use_ocr = use_ocr
        self.ocr_engine = ocr_engine
        self._paddleocr = None  # 延迟初始化
    
    def process_document(self, file_path: str, use_ocr: Optional[bool] = None, ocr_engine: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        处理文档并返回切分后的片段
        
        Args:
            file_path: 文档路径（支持 .docx 和 .pdf）
            use_ocr: 是否使用 OCR（None 表示自动检测）
            ocr_engine: OCR 引擎 ('paddleocr' 或 'qwen-vl')
            
        Returns:
            List[Dict]: 片段列表，每个片段包含：
                - id: 唯一标识
                - text: 文本内容
                - chapter: 所属章节
                - position: 位置信息
                - metadata: 元数据
        """
        if use_ocr is not None:
            self.use_ocr = use_ocr
        if ocr_engine is not None:
            self.ocr_engine = ocr_engine
            
        if file_path.endswith('.docx'):
            return self._process_word(file_path)
        elif file_path.endswith('.pdf'):
            if not PDF_SUPPORT:
                raise ImportError("PyPDF2 未安装，无法处理 PDF 文件")
            return self._process_pdf(file_path)
        else:
            raise ValueError(f"不支持的文件格式：{file_path}")
    
    def _process_word(self, file_path: str) -> List[Dict[str, Any]]:
        """处理 Word 文档"""
        doc = Document(file_path)
        fragments = []
        current_chapter = "引言"
        current_chapter_id = 0
        para_in_chapter = 0
        buffer_text = ""
        buffer_start_pos = 0
        
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue
            
            if self._is_heading(para):
                if buffer_text:
                    fragments.extend(self._create_fragments(
                        buffer_text, current_chapter, current_chapter_id,
                        buffer_start_pos, para_in_chapter
                    ))
                    buffer_text = ""
                
                current_chapter = text
                current_chapter_id += 1
                para_in_chapter = 0
                buffer_start_pos = i + 1
                continue
            
            if len(buffer_text) + len(text) <= self.max_fragment_length * 1.5:
                buffer_text += text + "\n"
            else:
                if buffer_text:
                    fragments.extend(self._create_fragments(
                        buffer_text, current_chapter, current_chapter_id,
                        buffer_start_pos, para_in_chapter
                    ))
                    para_in_chapter += 1
                buffer_text = text + "\n"
                buffer_start_pos = i
        
        if buffer_text:
            fragments.extend(self._create_fragments(
                buffer_text, current_chapter, current_chapter_id,
                buffer_start_pos, para_in_chapter
            ))
        
        return fragments
    
    def _process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """处理 PDF 文档"""
        fragments = []
        
        # 首先尝试直接提取文字
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            # 检查是否有可提取的文字
            has_text = False
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    has_text = True
                    break
            
            # 如果没有文字或强制使用 OCR
            if not has_text or self.use_ocr:
                print(f"PDF 无文字层或启用 OCR 模式，使用视觉模型识别...")
                return self._process_pdf_with_ocr(file_path)
            
            # 正常提取文字
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if not text.strip():
                    continue
                
                chapter = f"第 {page_num + 1} 页"
                page_fragments = self._create_fragments(
                    text, chapter, page_num + 1,
                    0, 0
                )
                
                for frag in page_fragments:
                    frag['id'] = f"page{page_num + 1}_{frag['id']}"
                    frag['page_number'] = page_num + 1
                    frag['total_pages'] = total_pages
                
                fragments.extend(page_fragments)
        
        return fragments
    
    def _process_pdf_with_ocr(self, file_path: str) -> List[Dict[str, Any]]:
        """使用 OCR 处理扫描版 PDF"""
        if not PDF2IMAGE_SUPPORT:
            raise ImportError("pdf2image 未安装，无法进行 OCR。请运行：pip install pdf2image")
        
        # 检查 OCR 引擎
        if self.ocr_engine == 'paddleocr':
            if not PADDLEOCR_SUPPORT:
                raise ImportError("PaddleOCR 未安装。请运行：pip install paddlepaddle paddleocr")
        elif self.ocr_engine == 'qwen-vl':
            if not DASHSCOPE_SUPPORT:
                raise ImportError("dashscope 未安装。请运行：pip install dashscope")
            api_key = os.environ.get('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")
        else:
            raise ValueError(f"不支持的 OCR 引擎：{self.ocr_engine}")
        
        fragments = []
        
        # 检查是否有缓存的 OCR 结果 - 使用固定的物理缓存目录
        # 缓存目录在项目根目录下的 cache/ocr/ 目录，确保重启后不会丢失
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_dir = os.path.join(project_root, 'cache', 'ocr')
        os.makedirs(cache_dir, exist_ok=True)
        
        # 使用文件内容的hash作为缓存文件名，确保同一文件不同上传路径也能命中缓存
        import hashlib
        print(f"正在计算文件哈希值用于缓存匹配...")
        file_hash = self._calculate_file_hash(file_path)
        
        # 缓存文件名格式: {hash}_{ocr_engine}_ocr.json
        # 不再包含文件名，因为文件名可能包含UUID而变化
        cache_file = os.path.join(cache_dir, f"{file_hash}_{self.ocr_engine}_ocr.json")
        
        # 兼容旧格式缓存文件（包含文件名的格式）
        if not os.path.exists(cache_file):
            # 查找以相同hash开头的旧格式缓存文件
            for existing_file in os.listdir(cache_dir):
                if existing_file.startswith(file_hash) and existing_file.endswith(f'_{self.ocr_engine}_ocr.json'):
                    cache_file = os.path.join(cache_dir, existing_file)
                    print(f"找到旧格式缓存文件: {existing_file}")
                    break
        
        print(f"缓存文件: {os.path.basename(cache_file)}")
        
        # 尝试加载缓存
        ocr_results = {}
        cache_fully_loaded = False
        if os.path.exists(cache_file):
            print(f"发现 OCR 缓存文件，正在加载...")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    ocr_results = json.load(f)
                print(f"已加载 {len(ocr_results)} 页的缓存结果")
                
                # 检查缓存是否完整（需要知道总页数）
                # 先快速获取PDF页数
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                
                # 检查是否所有页都有缓存
                all_pages_cached = all(
                    f"page_{i+1}" in ocr_results and ocr_results[f"page_{i+1}"].get('text')
                    for i in range(total_pages)
                )
                
                if all_pages_cached:
                    print(f"缓存完整！跳过 PDF 转图片和 OCR 识别步骤")
                    cache_fully_loaded = True
                else:
                    print(f"缓存不完整，需要处理缺失的页面")
                    
            except Exception as e:
                print(f"加载缓存失败: {e}")
                ocr_results = {}
        
        # 如果缓存不完整，需要转换PDF为图片进行OCR
        images = []
        if not cache_fully_loaded:
            print(f"正在将 PDF 转换为图片（使用 {self.ocr_engine} OCR）...")
            images = convert_from_path(file_path, dpi=200)
            total_pages = len(images)
        print(f"共 {total_pages} 页")
        
        # 逐页处理
        for page_num in range(total_pages):
            page_key = f"page_{page_num + 1}"
            
            # 检查是否已有缓存
            if page_key in ocr_results and ocr_results[page_key].get('text'):
                print(f"第 {page_num + 1}/{total_pages} 页使用缓存结果")
                text = ocr_results[page_key]['text']
            else:
                if cache_fully_loaded:
                    # 不应该到达这里，但以防万一
                    continue
                    
                print(f"正在识别第 {page_num + 1}/{total_pages} 页...")
                image = images[page_num]
                
                if self.ocr_engine == 'paddleocr':
                    text = self._ocr_with_paddleocr(image)
                else:
                    # 通义千问视觉模型
                    import io
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    text = self._ocr_with_vision_model(img_base64, os.environ.get('DASHSCOPE_API_KEY'))
                
                # 保存到缓存
                ocr_results[page_key] = {
                    'text': text,
                    'ocr_engine': self.ocr_engine
                }
                
                # 实时保存缓存
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(ocr_results, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"保存缓存失败: {e}")
            
            if not text or not text.strip():
                print(f"第 {page_num + 1} 页未识别到文字")
                continue
            
            chapter = f"第 {page_num + 1} 页"
            page_fragments = self._create_fragments(
                text, chapter, page_num + 1,
                0, 0
            )
            
            for frag in page_fragments:
                frag['id'] = f"page{page_num + 1}_{frag['id']}"
                frag['page_number'] = page_num + 1
                frag['total_pages'] = total_pages
                frag['metadata']['ocr'] = True
                frag['metadata']['ocr_engine'] = self.ocr_engine
            
            fragments.extend(page_fragments)
        
        return fragments
    
    def _calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        计算文件内容的 MD5 哈希值
        使用分块读取避免大文件内存问题
        """
        import hashlib
        hasher = hashlib.md5()
        
        # 获取文件大小用于显示进度
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        
        return hasher.hexdigest()[:16]
    
    def _ocr_with_paddleocr(self, image) -> str:
        """使用 PaddleOCR 进行识别"""
        try:
            # 延迟初始化 PaddleOCR
            if self._paddleocr is None:
                self._paddleocr = PaddleOCR(use_angle_cls=True, lang='ch')
            
            import numpy as np
            img_array = np.array(image)
            
            # 新版 PaddleOCR API
            result = self._paddleocr.ocr(img_array)
            
            if not result or not result[0]:
                return ""
            
            # 按位置排序，从上到下，从左到右
            lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    box = line[0]  # 坐标
                    text = line[1][0]  # 文字
                    # 获取 y 坐标（用于排序）
                    y_pos = min(p[1] for p in box)
                    x_pos = min(p[0] for p in box)
                    lines.append((y_pos, x_pos, text))
            
            # 按 y 坐标分组（同一行的文字）
            lines.sort(key=lambda x: (x[0], x[1]))
            
            # 合并文本，尝试保持段落结构
            text_parts = []
            current_y = None
            current_line = []
            
            for y, x, text in lines:
                if current_y is None or abs(y - current_y) < 15:  # 同一行
                    current_line.append(text)
                    current_y = y
                else:
                    if current_line:
                        text_parts.append(' '.join(current_line))
                    current_line = [text]
                    current_y = y
            
            if current_line:
                text_parts.append(' '.join(current_line))
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            print(f"PaddleOCR 识别错误: {e}")
            return ""
    
    def _ocr_with_vision_model(self, image_base64: str, api_key: str) -> str:
        """使用通义千问视觉模型进行 OCR"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:image/png;base64,{image_base64}"
                        },
                        {
                            "text": """请识别这张图片中的所有文字内容。

要求：
1. 按照原文的段落结构输出，保持段落之间的空行
2. 忽略页眉、页脚、页码等边角内容
3. 如果有标题，单独成行
4. 保持原文的标点符号
5. 只输出识别到的文字，不要添加任何解释或说明"""
                        }
                    ]
                }
            ]
            
            response = MultiModalConversation.call(
                model='qwen-vl-max',
                messages=messages,
                api_key=api_key
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content
                return result
            else:
                print(f"视觉模型调用失败: {response.code} - {response.message}")
                return ""
                
        except Exception as e:
            print(f"OCR 识别错误: {e}")
            return ""
    
    def _is_heading(self, paragraph) -> bool:
        """判断是否为标题"""
        if paragraph.style.name.startswith('Heading'):
            return True
        
        text = paragraph.text.strip()
        if len(text) > 50:
            return False
        
        heading_patterns = [
            r'^第[一二三四五六七八九十]+[章节篇部]',
            r'^[一二三四五六七八九十]+[、.]',
            r'^\d+[\.\、]',
            r'^[（(]\d+[)）]',
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _create_fragments(self, text: str, chapter: str, chapter_id: int,
                         start_pos: int, para_num: int) -> List[Dict[str, Any]]:
        """创建片段"""
        fragments = []
        sentences = self._split_sentences(text)
        
        current_fragment = ""
        fragment_sentences = []
        
        for sentence in sentences:
            if len(current_fragment) + len(sentence) <= self.max_fragment_length:
                current_fragment += sentence
                fragment_sentences.append(sentence)
            else:
                if current_fragment and len(current_fragment) >= self.min_fragment_length:
                    frag_id = f"chapter{chapter_id}_para{para_num + 1}_frag{len(fragments) + 1}"
                    fragments.append({
                        'id': frag_id,
                        'text': current_fragment.strip(),
                        'chapter': chapter,
                        'chapter_id': chapter_id,
                        'position': {
                            'start': start_pos,
                            'fragment_index': len(fragments)
                        },
                        'metadata': {
                            'length': len(current_fragment),
                            'sentence_count': len(fragment_sentences)
                        }
                    })
                
                current_fragment = sentence
                fragment_sentences = [sentence]
        
        if current_fragment and len(current_fragment) >= self.min_fragment_length:
            frag_id = f"chapter{chapter_id}_para{para_num + 1}_frag{len(fragments) + 1}"
            fragments.append({
                'id': frag_id,
                'text': current_fragment.strip(),
                'chapter': chapter,
                'chapter_id': chapter_id,
                'position': {
                    'start': start_pos,
                    'fragment_index': len(fragments)
                },
                'metadata': {
                    'length': len(current_fragment),
                    'sentence_count': len(fragment_sentences)
                }
            })
        
        # 兜底：如果没有片段但文本不为空，强制创建一个片段
        if not fragments and text.strip():
            frag_id = f"chapter{chapter_id}_para{para_num + 1}_frag1"
            fragments.append({
                'id': frag_id,
                'text': text.strip(),
                'chapter': chapter,
                'chapter_id': chapter_id,
                'position': {
                    'start': start_pos,
                    'fragment_index': 0
                },
                'metadata': {
                    'length': len(text.strip()),
                    'sentence_count': len(sentences)
                }
            })
        
        return fragments
    
    def _split_sentences(self, text: str) -> List[str]:
        """切分句子"""
        sentences = re.split(r'([。！？\n]+)', text)
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])
        
        if len(sentences) % 2 == 1 and sentences[-1]:
            result.append(sentences[-1])
        
        return [s for s in result if s.strip()]
    
    def save_fragments(self, fragments: List[Dict], output_path: str):
        """保存片段到 JSON 文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_fragments': len(fragments),
                'fragments': fragments
            }, f, ensure_ascii=False, indent=2)
    
    def load_fragments(self, input_path: str) -> List[Dict]:
        """从 JSON 文件加载片段"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['fragments']
