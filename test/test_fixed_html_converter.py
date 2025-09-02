#!/usr/bin/env python3
"""
测试修复后的 HTML 图片处理功能
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_html_converter import DoclingHtmlToMarkdownConverter

def test_fixed_html_image_processing():
    """测试修复后的 HTML 图片处理功能"""
    
    print("🧪 测试修复后的 HTML 图片处理功能")
    print("=" * 60)
    
    # 创建支持图片处理的转换器
    converter = DoclingHtmlToMarkdownConverter(
        minio_endpoint="10.3.70.127:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin", 
        minio_bucket="test-bucket",
        minio_secure=False,
        enable_image_processing=True
    )
    
    # 测试 URL
    test_url = "https://smartvision.dcclouds.com/docs/getting-started/overview/"
    
    print(f"🎯 测试 URL: {test_url}")
    
    try:
        # 开始转换
        markdown_content = converter.convert_html_url_to_markdown(test_url)
        
        print(f"\n📊 转换结果统计:")
        print(f"   Markdown 长度: {len(markdown_content)} 字符")
        
        # 统计 Markdown 中的图片链接
        import re
        image_links = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown_content)
        print(f"   图片链接数量: {len(image_links)}")
        
        if image_links:
            print(f"\n🖼️ 找到的图片链接:")
            for i, (alt_text, url) in enumerate(image_links[:5]):  # 只显示前5个
                print(f"   {i+1}. Alt: '{alt_text}' -> URL: {url}")
            if len(image_links) > 5:
                print(f"   ... 还有 {len(image_links) - 5} 个图片链接")
        
        # 检查 MinIO 链接
        minio_links = [link for _, link in image_links if "10.3.70.127:9000" in link]
        print(f"   MinIO 图片数量: {len(minio_links)}")
        
        if minio_links:
            print(f"\n✅ MinIO 图片上传成功的链接:")
            for i, link in enumerate(minio_links[:3]):  # 只显示前3个
                print(f"   {i+1}. {link}")
        
        # 保存结果到文件
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/fixed_html_test.md"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        # 测试结果评估
        if len(minio_links) > 0:
            print(f"\n🎉 测试成功！成功上传了 {len(minio_links)} 张图片到 MinIO")
        else:
            print(f"\n⚠️ 图片处理可能存在问题，没有找到 MinIO 链接")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_html_image_processing()
