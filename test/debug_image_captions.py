#!/usr/bin/env python3
"""
调试图片题注获取
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter

def debug_image_captions():
    """调试图片题注"""
    
    print("🔍 调试图片题注信息")
    print("=" * 60)
    
    # 初始化 Docling 转换器
    converter = DocumentConverter()
    
    # 测试文件
    test_file = str(project_root / "test" / "input" / "神码问学-知识中心设计.docx")
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print(f"📄 处理文件: {test_file}")
    
    try:
        # 转换文档
        result = converter.convert(test_file)
        doc = result.document
        
        # 查找所有图片
        # 使用正确的方法查找图片
        if hasattr(doc, 'pictures') and doc.pictures:
            pictures = doc.pictures
            print(f"🖼️ 发现 {len(pictures)} 张图片")
        else:
            pictures = []
            print("🖼️ 未发现图片")
        
        # 获取所有元素用于题注查找
        all_items = list(doc.iterate_items())
        
        for i, picture in enumerate(pictures):
            print(f"\n🔍 图片 {i+1} 详细信息:")
            print(f"   类型: {type(picture)}")
            
            # 检查题注相关属性
            caption_attrs = ['caption_text', 'captions', 'caption', 'title', 'alt_text', 'alt', 'description']
            
            for attr in caption_attrs:
                if hasattr(picture, attr):
                    value = getattr(picture, attr)
                    if callable(value):
                        try:
                            if attr == 'caption_text':
                                result = value(doc)  # caption_text 需要 doc 参数
                            else:
                                result = value()
                            print(f"   {attr}(): {result} (类型: {type(result)})")
                        except Exception as e:
                            print(f"   {attr}(): 调用失败 - {e}")
                    else:
                        print(f"   {attr}: {value} (类型: {type(value)})")
            
            # 检查 captions 列表的内容
            if hasattr(picture, 'captions') and picture.captions:
                print(f"   captions 内容:")
                for j, caption in enumerate(picture.captions):
                    print(f"     caption {j}: {caption}")
                    if hasattr(caption, 'text'):
                        print(f"       text: {caption.text}")
            
            # 检查 label 属性
            if hasattr(picture, 'label'):
                print(f"   label: {picture.label}")
            
            # 检查 prov 属性
            if hasattr(picture, 'prov'):
                print(f"   prov: {picture.prov}")
                
            # 检查 annotations 属性
            if hasattr(picture, 'annotations'):
                print(f"   annotations: {picture.annotations}")
                
            # 检查 children 属性
            if hasattr(picture, 'children'):
                print(f"   children: {picture.children}")
                if picture.children:
                    for j, child in enumerate(picture.children):
                        print(f"     child {j}: {child} (类型: {type(child)})")
                        # 检查子元素的文本内容
                        if hasattr(child, 'text'):
                            print(f"       text: {child.text}")
            
            # 检查父元素和兄弟元素
            if hasattr(picture, 'parent') and picture.parent:
                parent = picture.parent
                print(f"   parent: {parent} (类型: {type(parent)})")
                
                # 检查父元素的父元素
                if hasattr(parent, 'parent') and parent.parent:
                    grandparent = parent.parent
                    print(f"   grandparent: {grandparent} (类型: {type(grandparent)})")
                    
                    # 检查祖父元素的子元素，寻找可能的题注
                    if hasattr(grandparent, 'children') and grandparent.children:
                        print(f"   grandparent的子元素：")
                        for j, sibling in enumerate(grandparent.children):
                            print(f"     sibling {j}: {type(sibling).__name__}")
                            if hasattr(sibling, 'text') and sibling.text:
                                text = sibling.text.strip()
                                if text and len(text) < 200:  # 短文本可能是题注
                                    print(f"       可能的题注: {text}")
                
                # 检查父元素的兄弟元素
                if hasattr(parent, 'parent') and parent.parent and hasattr(parent.parent, 'children'):
                    siblings = parent.parent.children
                    print(f"   父元素的兄弟元素：")
                    for j, sibling in enumerate(siblings):
                        if sibling != parent:  # 不包括图片的直接父元素
                            print(f"     sibling {j}: {type(sibling).__name__}")
                            if hasattr(sibling, 'text') and sibling.text:
                                text = sibling.text.strip()
                                if text and any(keyword in text for keyword in ['图', 'Figure', 'Fig.', '图片', '示意图']):
                                    print(f"       ✅ 可能的题注: {text}")
        
        # 查找文档中所有的文本元素，看看是否有图片题注
        print(f"\n📝 查找可能的图片题注文本:")
        
        # 使用 Docling 的导出功能来获取 Markdown 文本
        try:
            markdown_text = doc.export_to_markdown()
            print(f"📄 Markdown 内容长度: {len(markdown_text)} 字符")
            
            # 查找包含图片关键词的行
            lines = markdown_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line and any(keyword in line for keyword in ['图', 'Figure', 'Fig.', '图片', '示意图', '流程图']):
                    print(f"   可能的题注行 {i}: {line}")
                    
                    # 检查周围的行
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line:
                            print(f"     前一行: {prev_line}")
                    if i < len(lines) - 1:
                        next_line = lines[i+1].strip()
                        if next_line:
                            print(f"     后一行: {next_line}")
            
            # 查找 <!-- image --> 注释附近的文本
            print(f"\n🖼️ 查找图片注释附近的文本:")
            for i, line in enumerate(lines):
                if '<!-- image -->' in line:
                    print(f"   找到图片注释在第 {i+1} 行")
                    
                    # 检查前后几行的文本
                    for offset in [-3, -2, -1, 1, 2, 3]:
                        check_line_idx = i + offset
                        if 0 <= check_line_idx < len(lines):
                            check_line = lines[check_line_idx].strip()
                            if check_line and not check_line.startswith('#') and len(check_line) < 100:
                                direction = "前" if offset < 0 else "后"
                                print(f"     {direction} {abs(offset)} 行: {check_line}")
                                # 检查是否包含图相关关键词
                                if any(keyword in check_line for keyword in ['图', 'Figure', 'Fig.', '图片', '示意图', '流程图']):
                                    print(f"       ✅ 可能是题注!")
                        
        except Exception as e:
            print(f"   ❌ 导出 Markdown 失败: {e}")
        
        # 尝试另一种方法：直接遍历文档的文本
        print(f"\n� 尝试遍历文档文本:")
        try:
            # 检查文档是否有 texts 属性
            if hasattr(doc, 'texts') and doc.texts:
                print(f"   找到 {len(doc.texts)} 个文本对象")
                for i, text_item in enumerate(doc.texts):
                    if hasattr(text_item, 'text') and text_item.text:
                        text = text_item.text.strip()
                        if text and len(text) < 200:  # 短文本可能是题注
                            print(f"   文本 {i}: {text}")
                            if any(keyword in text for keyword in ['图', 'Figure', 'Fig.', '图片', '示意图', '流程图']):
                                print(f"     ✅ 可能是题注!")
            
            # 检查文档是否有其他文本容器
            for attr in ['body', 'main_text', 'content']:
                if hasattr(doc, attr):
                    container = getattr(doc, attr)
                    print(f"   检查 doc.{attr}: {type(container)}")
                    
        except Exception as e:
            print(f"   ❌ 遍历文档文本失败: {e}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_captions()
