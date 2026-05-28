"""
超大文本处理 API
"""
import os
import sys
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from large_text_processor import (
    DocumentProcessor,
    BatchStyleExtractor,
    StyleIndex,
    RewriteAgent,
    QualityChecker
)

large_text_api = Blueprint('large_text', __name__)

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads', 'large_text')
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, 'outputs', 'large_text')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

task_status = {}
saved_analyses = {}


@large_text_api.route('/')
def index():
    """超大文本处理页面"""
    return render_template('large_text.html')


@large_text_api.route('/process_source', methods=['POST'])
def process_source():
    """处理源文档"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if not file:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        # 获取 OCR 参数
        use_ocr = request.form.get('use_ocr', 'false').lower() == 'true'
        ocr_engine = request.form.get('ocr_engine', 'paddleocr')
        
        # 获取模型参数
        model = request.form.get('model', 'deepseek-api:deepseek-v4-flash')
        
        # 获取 DeepSeek API Key（前端传入）
        deepseek_api_key = request.form.get('deepseek_api_key', '')
        
        # 获取部分片段分析参数
        partial_analysis = request.form.get('partial_analysis', 'false').lower() == 'true'
        analysis_ratio = float(request.form.get('analysis_ratio', '1.0'))
        
        # 获取原始文件名和扩展名
        original_filename = file.filename
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
        else:
            ext = 'docx'
        
        # 使用 UUID 作为文件名，保留扩展名
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        print(f"文件保存到: {file_path}, OCR 模式: {use_ocr}, OCR 引擎: {ocr_engine}, 模型: {model}", flush=True)
        
        analysis_id = str(uuid.uuid4())
        
        task_status[analysis_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在切分文档...',
            'file_path': file_path,
            'use_ocr': use_ocr,
            'ocr_engine': ocr_engine,
            'model': model,
            'deepseek_api_key': deepseek_api_key,
            'partial_analysis': partial_analysis,
            'analysis_ratio': analysis_ratio
        }
        
        from threading import Thread
        thread = Thread(target=process_source_task, args=(analysis_id, file_path, use_ocr, ocr_engine, model, deepseek_api_key, partial_analysis, analysis_ratio))
        thread.start()
        
        print(f"返回 analysis_id: {analysis_id}", flush=True)
        return jsonify({
            'success': True,
            'analysis_id': analysis_id
        })
        
    except Exception as e:
        import traceback
        print(f"=== process_source 错误 ===", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def process_source_task(analysis_id, file_path, use_ocr=False, ocr_engine='paddleocr', model='deepseek-api:deepseek-v4-flash', deepseek_api_key='', partial_analysis=False, analysis_ratio=1.0):
    """处理源文档任务
    
    Args:
        partial_analysis: 是否只分析部分片段
        analysis_ratio: 分析比例（0.1-1.0）
    """
    try:
        processor = DocumentProcessor(use_ocr=use_ocr, ocr_engine=ocr_engine)
        task_status[analysis_id]['message'] = '正在切分文档...' + ('（OCR 模式 - ' + ocr_engine + '）' if use_ocr else '')
        fragments = processor.process_document(file_path)
        
        # 检查是否有片段
        if not fragments or len(fragments) == 0:
            task_status[analysis_id]['status'] = 'failed'
            task_status[analysis_id]['error'] = '文档无法提取文本内容。可能原因：\n1. PDF 是扫描版（图片），没有文字层\n2. PDF 文件损坏\n3. 文档内容为空\n\n建议：尝试上传 Word 文档（.docx）格式'
            return
        
        task_status[analysis_id]['progress'] = 20
        
        total_fragments = len(fragments)
        task_status[analysis_id]['message'] = f'已切分为 {total_fragments} 个片段'
        
        # 部分片段分析：只选择部分片段进行分析
        analyzed_fragments = fragments
        skipped_indices = []
        
        if partial_analysis and analysis_ratio < 1.0:
            import random
            random.seed(42)  # 固定种子确保可重复
            
            # 计算要分析的片段数量
            analyze_count = max(1, int(total_fragments * analysis_ratio))
            
            # 均匀采样：从头、中、尾各取一部分
            if total_fragments > 0:
                # 头部取 30%，中部取 40%，尾部取 30%
                head_count = max(1, int(analyze_count * 0.3))
                tail_count = max(1, int(analyze_count * 0.3))
                mid_count = analyze_count - head_count - tail_count
                
                head_indices = list(range(0, min(head_count, total_fragments)))
                tail_start = max(0, total_fragments - tail_count)
                tail_indices = list(range(tail_start, total_fragments))
                
                mid_start = head_count
                mid_end = tail_start
                if mid_end > mid_start and mid_count > 0:
                    mid_step = max(1, (mid_end - mid_start) // mid_count)
                    mid_indices = list(range(mid_start, mid_end, mid_step))[:mid_count]
                else:
                    mid_indices = []
                
                selected_indices = sorted(set(head_indices + mid_indices + tail_indices))
                analyzed_fragments = [fragments[i] for i in selected_indices]
                skipped_indices = [i for i in range(total_fragments) if i not in selected_indices]
                
                task_status[analysis_id]['message'] = f'快速模式：分析 {len(analyzed_fragments)}/{total_fragments} 个片段（{int(analysis_ratio*100)}%）'
                print(f"部分片段分析：从 {total_fragments} 个片段中选择 {len(analyzed_fragments)} 个进行分析")
        
        task_status[analysis_id]['progress'] = 30
        task_status[analysis_id]['message'] = f'正在提取风格（模型: {model}）...'
        
        extractor = BatchStyleExtractor(model=model, deepseek_api_key=deepseek_api_key)
        progress_file = os.path.join(OUTPUT_FOLDER, f"{analysis_id}_progress.json")
        
        results = extractor.extract_batch(
            analyzed_fragments,
            batch_size=10,
            save_progress=True,
            progress_file=progress_file
        )
        
        task_status[analysis_id]['progress'] = 70
        task_status[analysis_id]['message'] = '正在建立索引...'
        
        # 如果是部分片段分析，需要将风格特征应用到所有片段
        if partial_analysis and skipped_indices:
            # 为跳过的片段设置全局风格（稍后在索引中处理）
            task_status[analysis_id]['message'] = f'建立索引（{len(results)} 个有风格，{len(skipped_indices)} 个使用全局风格）...'
        
        style_index = StyleIndex()
        style_index.build_index(results)
        
        # 保存所有片段信息（包括未分析的片段）
        style_index.all_fragments = fragments
        style_index.partial_analysis = partial_analysis
        style_index.analysis_ratio = analysis_ratio
        
        index_path = os.path.join(OUTPUT_FOLDER, f"{analysis_id}_index.json")
        style_index.save_index(index_path)
        
        chapters = list(set(f['chapter'] for f in fragments))
        avg_length = sum(len(f['text']) for f in fragments) / len(fragments) if fragments else 0
        
        task_status[analysis_id]['status'] = 'completed'
        task_status[analysis_id]['progress'] = 100
        task_status[analysis_id]['message'] = '处理完成！'
        task_status[analysis_id]['results'] = {
            'total_fragments': len(fragments),
            'analyzed_fragments': len(results),
            'total_chapters': len(chapters),
            'avg_length': round(avg_length, 0),
            'index_path': index_path,
            'partial_analysis': partial_analysis,
            'analysis_ratio': analysis_ratio
        }
        
    except Exception as e:
        import traceback
        print(f"=== process_source_task 错误 ===", flush=True)
        print(traceback.format_exc(), flush=True)
        task_status[analysis_id]['status'] = 'failed'
        task_status[analysis_id]['error'] = str(e)


@large_text_api.route('/process_target', methods=['POST'])
def process_target():
    """处理目标文档"""
    try:
        file = request.files['file']
        source_analysis_id = request.form.get('source_analysis_id')
        model = request.form.get('model', 'deepseek-api:deepseek-v4-flash')
        deepseek_api_key = request.form.get('deepseek_api_key', '')
        
        if not file:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        if not source_analysis_id:
            return jsonify({'success': False, 'error': '没有源分析 ID'}), 400
        
        original_filename = file.filename
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
        else:
            ext = 'docx'
        
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        task_id = str(uuid.uuid4())
        
        task_status[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在处理目标文档...',
            'file_path': file_path,
            'source_analysis_id': source_analysis_id,
            'model': model,
            'deepseek_api_key': deepseek_api_key
        }
        
        from threading import Thread
        thread = Thread(target=process_target_task, args=(task_id, file_path, source_analysis_id, model, deepseek_api_key))
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def process_target_task(task_id, file_path, source_analysis_id, model='deepseek-api:deepseek-v4-flash', deepseek_api_key=''):
    """处理目标文档任务"""
    try:
        processor = DocumentProcessor()
        task_status[task_id]['message'] = '正在切分目标文档...'
        fragments = processor.process_document(file_path)
        task_status[task_id]['progress'] = 20
        task_status[task_id]['message'] = f'已切分为 {len(fragments)} 个片段'
        
        index_path = task_status[source_analysis_id]['results']['index_path']
        style_index = StyleIndex()
        style_index.load_index(index_path)
        
        task_status[task_id]['progress'] = 30
        task_status[task_id]['message'] = '正在改写...'
        
        rewriter = RewriteAgent(model=model, deepseek_api_key=deepseek_api_key)
        progress_file = os.path.join(OUTPUT_FOLDER, f"{task_id}_rewrite_progress.json")
        
        rewrite_results = rewriter.rewrite_batch(
            fragments,
            style_index,
            batch_size=5,
            save_progress=True,
            progress_file=progress_file
        )
        
        task_status[task_id]['progress'] = 70
        task_status[task_id]['message'] = '正在进行质量检查...'
        
        checker = QualityChecker(model=model, deepseek_api_key=deepseek_api_key)
        quality_results = checker.check_batch(rewrite_results, batch_size=5)
        
        results_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_results.json")
        checker.save_results(quality_results, results_path)
        
        if quality_results['review_queue']:
            review_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_review.docx")
            checker.generate_review_document(quality_results['review_queue'], review_path)
        
        task_status[task_id]['status'] = 'completed'
        task_status[task_id]['progress'] = 100
        task_status[task_id]['message'] = '处理完成！'
        task_status[task_id]['results'] = quality_results
        
    except Exception as e:
        import traceback
        print(f"=== process_target_task 错误 ===", flush=True)
        print(traceback.format_exc(), flush=True)
        task_status[task_id]['status'] = 'failed'
        task_status[task_id]['error'] = str(e)


@large_text_api.route('/progress/<type>/<task_id>')
def get_progress(type, task_id):
    """获取进度"""
    if task_id not in task_status:
        return jsonify({
            'status': 'not_found',
            'error': '任务不存在'
        })
    
    status = task_status[task_id]
    
    return jsonify({
        'status': status['status'],
        'progress': status['progress'],
        'message': status['message'],
        'results': status.get('results'),
        'error': status.get('error')
    })


@large_text_api.route('/save_analysis', methods=['POST'])
def save_analysis():
    """保存分析结果"""
    try:
        data = request.json
        analysis_id = data['analysis_id']
        name = data['name']
        
        if analysis_id not in task_status:
            return jsonify({'success': False, 'error': '分析不存在'})
        
        status = task_status[analysis_id]
        
        if 'results' not in status:
            return jsonify({'success': False, 'error': '分析结果尚未生成，请等待处理完成'})
        
        saved_analyses[analysis_id] = {
            'id': analysis_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'total_fragments': status['results'].get('total_fragments', 0),
            'total_chapters': status['results'].get('total_chapters', 0),
            'index_path': status['results'].get('index_path', '')
        }
        
        saved_file = os.path.join(OUTPUT_FOLDER, 'saved_analyses.json')
        with open(saved_file, 'w', encoding='utf-8') as f:
            json.dump(saved_analyses, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@large_text_api.route('/saved_analyses')
def get_saved_analyses():
    """获取已保存的分析"""
    saved_file = os.path.join(OUTPUT_FOLDER, 'saved_analyses.json')
    
    if os.path.exists(saved_file):
        with open(saved_file, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
        return jsonify({'analyses': list(analyses.values())})
    
    return jsonify({'analyses': []})


@large_text_api.route('/style_labels/<analysis_id>')
def get_style_labels(analysis_id):
    """获取风格标签"""
    try:
        if analysis_id not in task_status:
            return jsonify({'success': False, 'error': '分析不存在'})
        
        index_path = task_status[analysis_id]['results']['index_path']
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        style_labels = index_data.get('global_style', {}).get('style_labels', [])
        
        return jsonify({
            'success': True,
            'style_labels': style_labels
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@large_text_api.route('/style_labels/<analysis_id>', methods=['POST'])
def update_style_labels(analysis_id):
    """更新风格标签"""
    try:
        if analysis_id not in task_status:
            return jsonify({'success': False, 'error': '分析不存在'})
        
        data = request.json
        new_style_labels = data.get('style_labels', [])
        
        index_path = task_status[analysis_id]['results']['index_path']
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        if 'global_style' not in index_data:
            index_data['global_style'] = {}
        
        index_data['global_style']['style_labels'] = new_style_labels
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@large_text_api.route('/export_results')
def export_results():
    """导出结果"""
    try:
        results_file = request.args.get('file')
        if not results_file:
            return jsonify({'error': '没有指定文件'}), 400
        
        file_path = os.path.join(OUTPUT_FOLDER, results_file)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
