#!/usr/bin/env python3
"""
测试 DoclingWordToMarkdownConverter 类
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.docling_word_converter import DoclingWordToMarkdownConverter


def test_local_file_conversion():
    """测试本地文件转换（模拟 URL 下载）"""
    print("=" * 60)
    print("测试本地文件转换")
    print("=" * 60)
    
    # MinIO 配置（需要根据实际情况修改）
    converter = DoclingWordToMarkdownConverter(
        minio_endpoint="localhost:9000",
        minio_access_key="minioadmin",  # 默认用户名
        minio_secret_key="minioadmin",  # 默认密码
        minio_bucket="test-documents",
        minio_secure=False,  # 本地开发环境
        image_url_prefix="http://localhost:9000"
    )
    
    print("✅ DoclingWordToMarkdownConverter 初始化成功")
    
    # 注意：这里需要一个真实的 Word 文档 URL 进行测试
    # 你可以：
    # 1. 使用本地文件服务器
    # 2. 使用在线测试文档
    # 3. 修改代码支持本地文件路径
    
    try:
        # 示例：使用在线文档（需要替换为实际可用的 URL）
        test_url = "https://example.com/test-document.docx"  # 替换为实际 URL
        
        print(f"🔄 开始转换文档: {test_url}")
        markdown_content = converter.convert_word_url_to_markdown(test_url)
        
        # 保存结果
        output_file = "test_output_from_url.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ 转换完成，结果已保存到: {output_file}")
        print(f"📄 Markdown 内容预览（前 500 字符）:")
        print("-" * 40)
        print(markdown_content[:500])
        if len(markdown_content) > 500:
            print("...")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 提示：请确保 MinIO 服务正在运行，并且提供了有效的文档 URL")


def test_with_local_file_server():
    """使用本地文件路径进行测试（需要先实现本地文件支持）"""
    print("=" * 60)
    print("建议的测试步骤")
    print("=" * 60)
    
    print("""
    要完整测试这个类，你需要：
    
    1. 🐳 启动 MinIO 服务：
       docker run -p 9000:9000 -p 9001:9001 \\
         -e "MINIO_ROOT_USER=minioadmin" \\
         -e "MINIO_ROOT_PASSWORD=minioadmin" \\
         minio/minio server /data --console-address ":9001"
    
    2. 📁 准备测试文档：
       - 将测试的 Word 文档上传到某个 HTTP 服务器
       - 或者修改类以支持本地文件路径
    
    3. 🔧 修改测试配置：
       - 更新 MinIO 连接参数
       - 提供有效的文档 URL
    
    4. 🧪 运行测试：
       python test_docling_word_converter.py
    """)


def create_enhanced_converter_with_local_support():
    """创建支持本地文件的增强版转换器"""
    print("=" * 60)
    print("创建支持本地文件的增强版本")
    print("=" * 60)
    
    enhanced_code = '''
# 在 DoclingWordToMarkdownConverter 类中添加这个方法：

def convert_local_word_to_markdown(self, word_file_path: str) -> str:
    """
    将本地 Word 文档转换为 Markdown 文本
    
    Args:
        word_file_path (str): 本地 Word 文档路径
        
    Returns:
        str: 转换后的 Markdown 文本
    """
    if not os.path.exists(word_file_path):
        raise FileNotFoundError(f"文件不存在: {word_file_path}")
    
    temp_dir = None
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"📁 创建临时目录: {temp_dir}")
        
        # 生成文档 ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        print(f"🔄 开始转换文档: {word_file_path}")
        
        # 使用 Docling 转换文档
        result = self.docling_converter.convert(word_file_path)
        doc = result.document
        
        # 提取并上传图片
        image_mapping = self._extract_and_upload_images(doc, temp_dir, doc_id)
        
        # 导出为 Markdown
        markdown_text = doc.export_to_markdown()
        
        # 替换图片链接
        if image_mapping:
            markdown_text = self._replace_images_in_markdown(markdown_text, image_mapping)
            print(f"✅ 已处理 {len(image_mapping)} 张图片")
        
        print(f"✅ 文档转换完成")
        return markdown_text
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        raise
    
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 清理临时目录: {temp_dir}")
'''
    
    print("建议添加的本地文件支持方法：")
    print(enhanced_code)


if __name__ == "__main__":
    print("🧪 DoclingWordToMarkdownConverter 测试")
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--local":
            test_with_local_file_server()
        elif sys.argv[1] == "--enhance":
            create_enhanced_converter_with_local_support()
    else:
        test_local_file_conversion()
        print()
        test_with_local_file_server()
