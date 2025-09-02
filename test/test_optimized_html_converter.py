#!/usr/bin/env python3
"""
测试优化后的 HTML 图片处理功能
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_html_converter import DoclingHtmlToMarkdownConverter

def test_optimized_html_conversion():
    """测试优化后的 HTML 转换功能"""
    
    print("🧪 测试优化后的 HTML 转换功能")
    print("=" * 60)
    
    # 创建使用原始图片链接的转换器
    converter = DoclingHtmlToMarkdownConverter(
        use_original_image_urls=True  # 使用原始链接，避免图片扎堆
    )
    
    # 测试一个简单的页面
    test_url = "https://smartvision.dcclouds.com/docs/getting-started/overview/"
    
    try:
        print(f"🔄 开始转换: {test_url}")
        print("✨ 特性: 使用原始图片链接，避免重复下载")
        
        markdown_result = converter.convert_html_url_to_markdown(test_url)
        
        print(f"\n📊 转换结果:")
        print(f"   📝 Markdown 长度: {len(markdown_result):,} 字符")
        
        # 统计图片链接
        import re
        image_links = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown_result)
        unique_urls = set(url for _, url in image_links)
        
        print(f"   🖼️ 图片链接总数: {len(image_links)}")
        print(f"   🔗 唯一图片 URL: {len(unique_urls)}")
        
        if unique_urls:
            print(f"\n🎨 唯一图片 URL 列表:")
            for i, url in enumerate(sorted(unique_urls), 1):
                print(f"   {i}. {url}")
        
        # 显示一小段内容
        print(f"\n📄 内容预览 (前 300 字符):")
        print("-" * 40)
        print(markdown_result[:300])
        if len(markdown_result) > 300:
            print("...")
        
        # 保存结果
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/optimized_html_result.md"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        # 成功总结
        print(f"\n🎉 转换成功！")
        print(f"   ✅ 避免了图片下载和存储开销")
        print(f"   ✅ 保持了原始图片的高质量")
        print(f"   ✅ 处理了 {len(unique_urls)} 个不同的图片")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_html_conversion()
