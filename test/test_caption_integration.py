#!/usr/bin/env python3
"""
测试集成了题注检测的 Docling Word 转换器
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_word_converter import DoclingWordToMarkdownConverter

def test_caption_detection():
    """测试题注检测功能"""
    
    # 配置转换器
    converter = DoclingWordToMarkdownConverter(
        minio_endpoint="10.3.70.127:9000",
        minio_access_key="minioadmin", 
        minio_secret_key="minioadmin",
        minio_bucket="md-images",
        minio_secure=False,
        image_url_prefix="http://10.3.70.127:9000"
    )
    
    # 测试文件路径
    test_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/input/企业AI 知识文档治理规范性建议.docx"
    
    print("🧪 测试题注检测功能")
    print(f"📄 测试文件: {test_file}")
    print("-" * 80)
    
    try:
        # 转换文档
        markdown_content = converter.convert_local_word_to_markdown(test_file)
        
        print("\n📋 转换结果:")
        print("-" * 40)
        
        # 显示前 2000 字符
        if len(markdown_content) > 2000:
            print(markdown_content[:2000])
            print(f"\n... (还有 {len(markdown_content) - 2000} 个字符)")
        else:
            print(markdown_content)
            
        # 检查图片链接
        print("\n🔍 图片链接分析:")
        print("-" * 40)
        
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if '![' in line and '](' in line:
                print(f"第 {i+1} 行: {line}")
        
        # 保存结果
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/test_caption_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_caption_detection()
