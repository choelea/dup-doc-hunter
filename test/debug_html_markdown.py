#!/usr/bin/env python3
"""
调试 HTML 到 Markdown 的图片处理
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_html_converter import DoclingHtmlToMarkdownConverter
import re

def debug_html_markdown_conversion():
    """调试 HTML 到 Markdown 的图片处理"""
    
    print("🔍 调试 HTML 到 Markdown 的图片处理")
    print("=" * 60)
    
    # 创建转换器（不启用图片处理，先看基础转换）
    converter = DoclingHtmlToMarkdownConverter()
    
    # 测试 URL
    test_url = "https://smartvision.dcclouds.com/docs/getting-started/overview/"
    
    try:
        # 获取 HTML 内容
        html_content = converter._fetch_html_from_url(test_url)
        
        print(f"🔍 HTML 内容分析:")
        print(f"   总长度: {len(html_content)} 字符")
        
        # 查找 HTML 中的图片标签
        img_tags = re.findall(r'<img[^>]*>', html_content, re.IGNORECASE)
        print(f"   img 标签数量: {len(img_tags)}")
        
        if img_tags:
            print(f"\n📸 HTML 中的图片标签:")
            for i, tag in enumerate(img_tags):
                print(f"   {i+1}. {tag}")
                
                # 提取 src 属性
                src_match = re.search(r'src=["\'](.*?)["\']', tag, re.IGNORECASE)
                if src_match:
                    src_url = src_match.group(1)
                    print(f"      src: {src_url}")
        
        # 转换为 Markdown（不处理图片）
        markdown = converter.convert_html_url_to_markdown(test_url)
        
        print(f"\n📝 Markdown 内容分析:")
        print(f"   总长度: {len(markdown)} 字符")
        
        # 查找 Markdown 中的图片语法
        md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
        print(f"   Markdown 图片数量: {len(md_images)}")
        
        if md_images:
            print(f"\n🖼️ Markdown 中的图片:")
            for i, (alt, url) in enumerate(md_images):
                print(f"   {i+1}. ![{alt}]({url})")
        else:
            print(f"\n❌ Markdown 中没有找到图片语法")
            
            # 检查是否有其他形式的图片引用
            img_refs = re.findall(r'image[_-]?\d*', markdown, re.IGNORECASE)
            if img_refs:
                print(f"   但找到了图片引用: {img_refs}")
                
                # 显示包含图片引用的行
                lines = markdown.split('\n')
                for line_num, line in enumerate(lines):
                    if any(ref in line.lower() for ref in [ref.lower() for ref in img_refs]):
                        print(f"   第{line_num+1}行: {line.strip()}")
            
            # 查找可能的图片占位符
            placeholders = re.findall(r'<!--.*?image.*?-->', markdown, re.IGNORECASE)
            if placeholders:
                print(f"   找到图片占位符: {placeholders}")
        
        # 保存详细的调试信息
        debug_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/debug_html_markdown.txt"
        os.makedirs(os.path.dirname(debug_file), exist_ok=True)
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("HTML 图片标签:\n")
            f.write("=" * 40 + "\n")
            for i, tag in enumerate(img_tags):
                f.write(f"{i+1}. {tag}\n")
            
            f.write(f"\n\nMarkdown 内容:\n")
            f.write("=" * 40 + "\n")
            f.write(markdown)
        
        print(f"\n💾 调试信息已保存到: {debug_file}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_markdown_conversion()
