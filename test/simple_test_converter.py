#!/usr/bin/env python3
"""
简单测试 DoclingWordToMarkdownConverter 类（使用本地文件）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_local_file_without_minio():
    """测试本地文件转换（不需要 MinIO）"""
    print("=" * 60)
    print("测试本地文件转换（模拟 MinIO）")
    print("=" * 60)
    
    try:
        from core.docling_word_converter import DoclingWordToMarkdownConverter
        
        # 使用虚拟的 MinIO 配置（用于初始化，但不会真正连接）
        converter = DoclingWordToMarkdownConverter(
            minio_endpoint="localhost:9000",
            minio_access_key="test",
            minio_secret_key="test",
            minio_bucket="test-bucket",
            minio_secure=False
        )
        
        print("✅ DoclingWordToMarkdownConverter 初始化成功")
        
        # 测试本地文件
        test_files = [
            "input/sample.docx",
            "input/企业AI 知识文档治理规范性建议.docx"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"\n🔄 测试文件: {test_file}")
                try:
                    # 注意：这里会尝试连接 MinIO，如果没有运行会失败
                    markdown_content = converter.convert_local_word_to_markdown(test_file)
                    
                    # 保存结果
                    output_file = f"output/test_{Path(test_file).stem}_docling.md"
                    os.makedirs("output", exist_ok=True)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    print(f"✅ 转换完成: {output_file}")
                    print(f"📄 内容预览（前 200 字符）:")
                    print("-" * 40)
                    print(markdown_content[:200])
                    if len(markdown_content) > 200:
                        print("...")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"❌ 转换失败: {e}")
                    if "Connection refused" in str(e) or "MinIO" in str(e):
                        print("💡 提示：需要启动 MinIO 服务才能完整测试图片上传功能")
                        return False
            else:
                print(f"⚠️ 测试文件不存在: {test_file}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请先安装 minio 库：pip install minio")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_docling_only():
    """仅测试 Docling 转换功能（不涉及 MinIO）"""
    print("=" * 60)
    print("仅测试 Docling 转换功能")
    print("=" * 60)
    
    try:
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        print("✅ Docling DocumentConverter 初始化成功")
        
        test_files = [
            "input/sample.docx",
            "input/企业AI 知识文档治理规范性建议.docx"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"\n🔄 测试文件: {test_file}")
                try:
                    # 使用 Docling 转换
                    result = converter.convert(test_file)
                    doc = result.document
                    markdown_text = doc.export_to_markdown()
                    
                    # 保存结果
                    output_file = f"output/test_{Path(test_file).stem}_docling_only.md"
                    os.makedirs("output", exist_ok=True)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_text)
                    
                    print(f"✅ 转换完成: {output_file}")
                    print(f"📊 文档信息:")
                    print(f"   - 字符数: {len(markdown_text)}")
                    
                    # 检查是否有图片
                    if hasattr(doc, 'pictures') and doc.pictures:
                        print(f"   - 图片数量: {len(doc.pictures)}")
                    else:
                        print("   - 无图片或图片信息不可用")
                    
                    print(f"📄 内容预览（前 300 字符）:")
                    print("-" * 40)
                    print(markdown_text[:300])
                    if len(markdown_text) > 300:
                        print("...")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"❌ 转换失败: {e}")
            else:
                print(f"⚠️ 测试文件不存在: {test_file}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请先安装 docling 库")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🧪 DoclingWordToMarkdownConverter 测试")
    
    # 切换到测试目录
    os.chdir(Path(__file__).parent)
    
    # 先测试纯 Docling 功能
    print("\n" + "="*60)
    print("第一步：测试纯 Docling 转换功能")
    print("="*60)
    
    docling_success = test_docling_only()
    
    if docling_success:
        print("\n" + "="*60)
        print("第二步：测试完整的转换器类（包含 MinIO）")
        print("="*60)
        test_local_file_without_minio()
    
    print("\n🏁 测试完成")
