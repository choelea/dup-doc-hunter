#!/usr/bin/env python3
"""
调试 HTML 图片对象结构
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_html_converter import DoclingHtmlToMarkdownConverter
import tempfile

def debug_html_images():
    """调试 HTML 图片对象结构"""
    
    print("🔍 调试 HTML 图片对象结构")
    print("=" * 60)
    
    # 创建转换器
    converter = DoclingHtmlToMarkdownConverter()
    
    # 简单的测试 HTML（带图片）
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>图片测试</title>
    </head>
    <body>
        <h1>图片测试</h1>
        <p>第一张图片：</p>
        <img src="https://via.placeholder.com/300x200/0066CC/FFFFFF?text=Test+Image+1" alt="测试图片1">
        <p>第二张图片：</p>
        <img src="https://httpbin.org/image/png" alt="测试图片2">
        <p>第三张图片（相对路径）：</p>
        <img src="/static/logo.png" alt="Logo">
    </body>
    </html>
    """
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"📁 创建临时目录: {temp_dir}")
        
        # 保存 HTML 到临时文件
        html_file_path = converter._save_html_to_temp_file(test_html, temp_dir)
        
        # 使用 Docling 转换
        result = converter.docling_converter.convert(html_file_path)
        doc = result.document
        
        print(f"\n📄 文档转换完成")
        print(f"   文档类型: {type(doc)}")
        print(f"   文档属性: {dir(doc)}")
        
        # 检查图片
        if hasattr(doc, 'pictures') and doc.pictures:
            print(f"\n🖼️ 发现 {len(doc.pictures)} 张图片")
            
            for i, picture in enumerate(doc.pictures):
                print(f"\n🔍 图片 {i+1} 详细信息:")
                print(f"   类型: {type(picture)}")
                print(f"   属性列表: {dir(picture)}")
                
                # 检查所有属性的值
                if hasattr(picture, '__dict__'):
                    print(f"   实例属性:")
                    for attr_name, attr_value in picture.__dict__.items():
                        print(f"     {attr_name}: {repr(attr_value)} (类型: {type(attr_value)})")
                
                # 检查特定的可能包含图片信息的属性
                interesting_attrs = ['src', 'uri', 'url', 'href', 'path', 'image', 'data', 'content', 'alt', 'title']
                print(f"   关键属性检查:")
                for attr_name in interesting_attrs:
                    if hasattr(picture, attr_name):
                        attr_value = getattr(picture, attr_name)
                        print(f"     {attr_name}: {repr(attr_value)} (类型: {type(attr_value)})")
                    else:
                        print(f"     {attr_name}: 不存在")
                
                # 检查方法 - 避免访问某些特殊属性
                methods = []
                for method_name in dir(picture):
                    if (not method_name.startswith('_') and 
                        method_name not in ['__signature__', '__fields__', '__fields_set__']):
                        try:
                            method_obj = getattr(picture, method_name)
                            if callable(method_obj):
                                methods.append(method_name)
                        except Exception:
                            pass  # 跳过无法访问的属性
                print(f"   可用方法: {methods}")
                
                # 尝试调用一些方法
                if hasattr(picture, 'get_image'):
                    try:
                        result1 = picture.get_image(doc)
                        print(f"   get_image(doc) 结果: {type(result1)} - {repr(result1)}")
                    except Exception as e:
                        print(f"   get_image(doc) 失败: {e}")
                    
                    # 不再尝试无参数的 get_image()，因为它需要 doc 参数
        else:
            print("\n📷 没有找到图片对象")
        
        # 检查原始 HTML 中的图片
        print(f"\n🔍 原始 HTML 图片标签分析:")
        import re
        img_tags = re.findall(r'<img[^>]*>', test_html, re.IGNORECASE)
        for i, img_tag in enumerate(img_tags):
            print(f"   图片 {i+1}: {img_tag}")
            
            # 提取 src 属性
            src_match = re.search(r'src=["\'](.*?)["\']', img_tag, re.IGNORECASE)
            if src_match:
                src_url = src_match.group(1)
                print(f"     源URL: {src_url}")
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 清理临时目录: {temp_dir}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_images()
