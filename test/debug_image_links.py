#!/usr/bin/env python3
"""
调试图片链接替换问题
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.docling_word_converter import DoclingWordToMarkdownConverter

def debug_image_replacement():
    """调试图片替换问题"""
    
    # MinIO 配置
    MINIO_ENDPOINT = "10.3.70.127:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_BUCKET = "md-images"
    
    print("🔧 调试图片链接替换")
    print("=" * 60)
    
    try:
        # 初始化转换器
        converter = DoclingWordToMarkdownConverter(
            minio_endpoint=MINIO_ENDPOINT,
            minio_access_key=MINIO_ACCESS_KEY,
            minio_secret_key=MINIO_SECRET_KEY,
            minio_bucket=MINIO_BUCKET,
            minio_secure=False  # 禁用 SSL
        )
        
        # 测试文件
        test_file = str(project_root / "test" / "input" / "神码问学-知识中心设计.docx")
        if not os.path.exists(test_file):
            print(f"❌ 测试文件不存在: {test_file}")
            return
        
        print(f"📄 处理文件: {test_file}")
        
        # 修改转换器以增加调试输出
        # 我们需要临时修改 _replace_images_in_markdown 方法
        original_replace_method = converter._replace_images_in_markdown
        
        def debug_replace_images_in_markdown(markdown_text, image_mapping):
            print(f"\n🔍 调试图片替换:")
            print(f"   图片映射: {image_mapping}")
            print(f"   Markdown 文本长度: {len(markdown_text)}")
            
            # 查找所有可能的图片引用
            img_patterns = [
                r'!\[[^\]]*\]\([^)]+\)',  # ![alt](url)
                r'<img[^>]*>',  # <img ...>
                r'image_\d+',  # image_数字
            ]
            
            print(f"   查找图片引用模式:")
            for pattern in img_patterns:
                matches = re.findall(pattern, markdown_text, re.IGNORECASE)
                if matches:
                    print(f"     模式 '{pattern}' 找到: {matches}")
            
            # 查找包含 image 的行
            print(f"   包含 'image' 的行:")
            lines = markdown_text.split('\n')
            for i, line in enumerate(lines):
                if 'image' in line.lower():
                    print(f"     第{i+1}行: {line.strip()}")
            
            # 调用原始方法
            result = original_replace_method(markdown_text, image_mapping)
            
            print(f"   替换后 MinIO 链接数量: {result.count('http://10.3.70.127:9000')}")
            
            return result
        
        # 替换方法
        converter._replace_images_in_markdown = debug_replace_images_in_markdown
        
        # 执行转换
        markdown_content = converter.convert_local_word_to_markdown(test_file)
        
        # 保存结果
        output_file = str(project_root / "test" / "output" / "debug_result.md")
        os.makedirs(str(project_root / "test" / "output"), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\n✅ 调试完成，结果保存到: {output_file}")
        print(f"📊 最终 MinIO 链接数量: {markdown_content.count('http://10.3.70.127:9000')}")
        
        # 显示前 500 字符
        print(f"\n📄 内容预览:")
        print("-" * 40)
        print(markdown_content[:500])
        if len(markdown_content) > 500:
            print("...")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_replacement()
