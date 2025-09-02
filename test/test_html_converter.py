#!/usr/bin/env python3
"""
测试 Docling HTML 转换器功能
"""

import sys
import os
sys.path.append('/Users/joe/codes/gitee/dup-doc-hunter')

from core.docling_html_converter import DoclingHtmlToMarkdownConverter

def test_basic_html_conversion():
    """测试基础 HTML 转换功能（不处理图片）"""
    
    print("🧪 测试基础 HTML 转换功能")
    print("=" * 60)
    
    # 创建基础转换器（不处理图片）
    converter = DoclingHtmlToMarkdownConverter()
    
    # 测试 HTML 内容转换
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试页面</title>
    </head>
    <body>
        <h1>欢迎使用 Docling HTML 转换器</h1>
        <h2>功能特性</h2>
        <ul>
            <li>支持 HTML 到 Markdown 转换</li>
            <li>可选的图片处理功能</li>
            <li>支持 MinIO 对象存储</li>
        </ul>
        
        <h2>使用方法</h2>
        <p>这是一个简单的使用示例：</p>
        <ol>
            <li>创建转换器实例</li>
            <li>调用转换方法</li>
            <li>获取 Markdown 结果</li>
        </ol>
        
        <blockquote>
            <p>这是一个引用块的示例</p>
        </blockquote>
        
        <table>
            <tr>
                <th>功能</th>
                <th>状态</th>
            </tr>
            <tr>
                <td>HTML 转换</td>
                <td>✅ 支持</td>
            </tr>
            <tr>
                <td>图片处理</td>
                <td>⚙️ 可选</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        print("🔄 开始转换 HTML 内容...")
        markdown_result = converter.convert_html_content_to_markdown(test_html)
        
        print("\n📋 转换结果:")
        print("-" * 40)
        print(markdown_result)
        
        # 保存结果
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/html_conversion_result.md"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()

def test_html_url_conversion():
    """测试 HTML URL 转换功能"""
    
    print("\n🧪 测试 HTML URL 转换功能")
    print("=" * 60)
    
    # 创建使用原始图片链接的转换器（推荐用于 HTML）
    converter = DoclingHtmlToMarkdownConverter(
            # 不需要配置 MinIO，因为我们使用原始链接
            use_original_image_urls=True  # 关键配置：使用原始图片链接
        )
    
    # 测试一个包含图片的网页
    test_url = "https://smartvision.dcclouds.com/doc/work/knowledge.html"
    
    try:
        print(f"🔄 开始转换 URL: {test_url}")
        print("🔗 使用原始图片链接模式（避免图片扎堆问题）")
        
        markdown_result = converter.convert_html_url_to_markdown(test_url)
        
        print("\n📋 转换结果统计:")
        print(f"   Markdown 总长度: {len(markdown_result)} 字符")
        
        # 统计图片链接
        import re
        image_links = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown_result)
        print(f"   图片链接数量: {len(image_links)}")
        
        if image_links:
            print(f"\n🖼️ 找到的图片链接:")
            for i, (alt_text, url) in enumerate(image_links):
                print(f"   {i+1}. Alt: '{alt_text}' -> URL: {url}")
        else:
            print("   没有找到图片链接")
        
        # 显示部分内容
        print("\n📋 Markdown 内容预览:")
        print("-" * 40)
        # 只显示前 500 字符
        if len(markdown_result) > 500:
            print(markdown_result[:500])
            print(f"\n... (还有 {len(markdown_result) - 500} 个字符)")
        else:
            print(markdown_result)
        
        # 保存结果
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/html_url_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        print(f"\n💾 结果已保存到: {output_file}")
        
        # 验证结果
        if len(image_links) > 0:
            print(f"\n✅ 成功！找到 {len(image_links)} 张图片，使用原始链接")
        else:
            print(f"\n ℹ️ 没有找到图片，或者图片处理存在问题")
        
    except Exception as e:
        print(f"❌ URL 转换失败: {e}")
        import traceback
        traceback.print_exc()

def test_html_with_minio():
    """测试带 MinIO 图片处理的 HTML 转换"""
    
    print("\n🧪 测试带 MinIO 图片处理的 HTML 转换")
    print("=" * 60)
    
    try:
        # 创建带图片处理的转换器
        converter = DoclingHtmlToMarkdownConverter(
            minio_endpoint="10.3.70.127:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket="html-images",
            minio_secure=False,
            image_url_prefix="http://10.3.70.127:9000",
            enable_image_processing=True
        )
        
        # 测试包含图片的 HTML
        test_html_with_image = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>带图片的测试页面</title>
        </head>
        <body>
            <h1>图片处理测试</h1>
            <p>这是一个测试页面，包含图片：</p>
            <img src="https://via.placeholder.com/300x200/0066CC/FFFFFF?text=Test+Image" alt="测试图片">
            <p>图片上方是一张占位符图片。</p>
        </body>
        </html>
        """
        
        print("🔄 开始转换包含图片的 HTML...")
        markdown_result = converter.convert_html_content_to_markdown(test_html_with_image)
        
        print("\n📋 转换结果:")
        print("-" * 40)
        print(markdown_result)
        
        # 保存结果
        output_file = "/Users/joe/codes/gitee/dup-doc-hunter/test/output/html_with_images_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ MinIO 图片处理测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Docling HTML 转换器测试开始")
    print("=" * 80)
    
    # 测试基础功能
    # test_basic_html_conversion()
    
    # 测试 URL 转换
    test_html_url_conversion()
    
    # 测试 MinIO 图片处理（如果 MinIO 可用）
    # test_html_with_minio()
    
    print("\n✅ 所有测试完成")
