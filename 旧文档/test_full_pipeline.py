"""
测试完整的文档处理流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from large_text_processor.document_processor import DocumentProcessor
from large_text_processor.style_extractor_batch import BatchStyleExtractor
from large_text_processor.style_index import StyleIndex

API_KEY = "sk-94b290c6b6324c36b8da09cc479c009e"

def test_full_pipeline():
    print("=" * 60)
    print("测试完整文档处理流程")
    print("=" * 60)
    
    # 测试文本（模拟一个文档，需要足够长才能切分）
    test_text = """
国立中正大学筹办过程中，熊式辉主持筹办工作，将国立中正大学筹办列为其政务的头等大事。他雷厉风行地推进各项筹备工作，同时十分注重延揽人才，亲自出面聘请了一批知名学者担任教授。筹备委员会成立后，立即着手制定办学方针和院系设置方案。经过反复论证，最终确定了以文理法工四学院为主体的办学架构。各学院设置合理，课程体系完善，为学校后续发展奠定了坚实基础。

第一章 肇基之艰

国立中正大学的创办，是江西高等教育史上的重要里程碑。1940年，在抗战烽火中，这所大学应运而生。首任校长胡先骕先生以其深厚的学术造诣和卓越的组织才能，为学校的发展奠定了坚实基础。在他的主持下，学校延揽了大批知名学者，如陈布雷、蒋廷黻、王世杰、何廉、甘乃光等人担任教授或评议员。这些学者在各自的领域都有卓越建树，为学校的教学科研工作注入了强大动力。

学校的办学宗旨是"培养国家建设人才，弘扬民族文化精神"。在这一宗旨指导下，学校确立了严谨治学、求真务实的学风。各院系课程设置既注重基础理论的传授，又强调实际应用能力的培养，形成了理论与实践并重的教学特色。学生在校期间，不仅要掌握扎实的专业知识，还要参与各种实践活动，培养解决实际问题的能力。

第二章 和合求新

随着时代变迁，学校经历了多次院系调整。1950年代，在全国高校院系调整中，国立中正大学的相关院系分别并入其他高校。然而，其办学精神和学术传统并未消逝，而是在新的体制下得到了延续和发展。许多校友在各自的岗位上继续发光发热，为国家建设贡献力量。

南昌大学时期，学校继承了国立中正大学的优良传统，在新的历史条件下开拓创新。学校坚持"实事求是、敢为人先"的校训，培养了大批优秀人才，为国家建设和社会发展作出了重要贡献。在新的历史时期，学校不断深化教育改革，提高教学质量，科研水平稳步提升，综合实力显著增强。

第三章 继往开来

进入新世纪，学校迎来了新的发展机遇。在"双一流"建设背景下，学校制定了新的发展战略，明确了建设高水平大学的目标。学校加大人才引进力度，优化师资队伍结构，提升科研创新能力，拓展国际合作交流。各项事业蓬勃发展，呈现出欣欣向荣的景象。

学校始终坚持立德树人的根本任务，注重培养学生的创新精神和实践能力。通过深化课程改革、完善培养体系、强化实践环节，不断提高人才培养质量。毕业生以基础扎实、作风朴实、工作踏实著称，受到用人单位的广泛好评。
"""
    
    # 1. 文档切分
    print("\n【步骤1】文档切分")
    processor = DocumentProcessor()
    
    # 保存测试文本到临时 docx 文件
    import tempfile
    from docx import Document as DocxDocument
    
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        temp_file = f.name
    
    doc = DocxDocument()
    for para in test_text.strip().split('\n\n'):
        if para.strip():
            doc.add_paragraph(para.strip())
    doc.save(temp_file)
    
    fragments = processor.process_document(temp_file)
    os.unlink(temp_file)
    
    print(f"  切分为 {len(fragments)} 个片段")
    
    if len(fragments) == 0:
        print("  警告：没有切分出任何片段，跳过后续测试")
        return
    
    for i, f in enumerate(fragments):
        print(f"  片段{i+1}: {len(f['text'])} 字符")
    
    # 2. 风格提取
    print("\n【步骤2】风格提取")
    extractor = BatchStyleExtractor(model='deepseek-api:deepseek-v4-flash', deepseek_api_key=API_KEY)
    
    import time
    start = time.time()
    
    results = extractor.extract_batch(fragments, batch_size=5)
    
    elapsed = time.time() - start
    print(f"  提取完成，耗时: {elapsed:.2f} 秒")
    print(f"  平均每个片段: {elapsed/len(fragments):.2f} 秒")
    
    # 3. 建立索引
    print("\n【步骤3】建立索引")
    style_index = StyleIndex()
    style_index.build_index(results)
    
    # 4. 查看全局风格
    print("\n【步骤4】全局风格")
    global_style = style_index.global_style
    print(f"  总片段数: {global_style.get('total_fragments', 'N/A')}")
    print(f"  有风格特征的片段: {global_style.get('fragments_with_style', 'N/A')}")
    print(f"  风格标签数: {len(global_style.get('style_labels', []))}")
    
    print("\n  风格标签:")
    for label in global_style.get('style_labels', [])[:5]:
        print(f"    - {label.get('label', 'N/A')}: {label.get('score', 'N/A')}分 (出现{label.get('frequency', 0)}次)")
    
    print("\n  例句:")
    for i, example in enumerate(global_style.get('example_fragments', [])[:3]):
        print(f"    {i+1}. {example[:100]}...")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_pipeline()
