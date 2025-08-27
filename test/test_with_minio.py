#!/usr/bin/env python3
"""
使用真实 MinIO 服务测试 DoclingWordToMarkdownConverter 类
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.docling_word_converter import DoclingWordToMarkdownConverter


def test_with_real_minio():
    """使用真实的 MinIO 服务测试"""
    print("=" * 60)
    print("使用真实 MinIO 服务测试 DoclingWordToMarkdownConverter")
    print("=" * 60)
    
    # MinIO 配置
    MINIO_ENDPOINT = "10.3.70.127:9000"  # 去掉 http:// 前缀
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_BUCKET = "md-images"
    
    try:
        # 初始化转换器
        converter = DoclingWordToMarkdownConverter(
            minio_endpoint=MINIO_ENDPOINT,
            minio_access_key=MINIO_ACCESS_KEY,
            minio_secret_key=MINIO_SECRET_KEY,
            minio_bucket=MINIO_BUCKET,
            minio_secure=False,  # HTTP 连接
            image_url_prefix=f"http://{MINIO_ENDPOINT}"  # 自定义 URL 前缀
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
                    # 转换文档
                    markdown_content = converter.convert_local_word_to_markdown(test_file)
                    
                    # 保存结果
                    output_file = f"output/test_{Path(test_file).stem}_with_minio.md"
                    os.makedirs("output", exist_ok=True)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    print(f"✅ 转换完成: {output_file}")
                    
                    # 检查是否有图片链接被替换
                    if "http://10.3.70.127:9000" in markdown_content:
                        image_count = markdown_content.count("http://10.3.70.127:9000")
                        print(f"🖼️ 发现 {image_count} 个 MinIO 图片链接")
                    
                    print(f"📄 内容预览（前 300 字符）:")
                    print("-" * 40)
                    print(markdown_content[:300])
                    if len(markdown_content) > 300:
                        print("...")
                    print("-" * 40)
                    
                    # 显示文件大小
                    file_size = len(markdown_content.encode('utf-8'))
                    print(f"📊 文件大小: {file_size} 字节")
                    
                except Exception as e:
                    print(f"❌ 转换失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️ 测试文件不存在: {test_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_minio_connection():
    """测试 MinIO 连接"""
    print("=" * 60)
    print("测试 MinIO 连接")
    print("=" * 60)
    
    try:
        from minio import Minio
        from minio.error import S3Error
        
        # MinIO 配置
        MINIO_ENDPOINT = "10.3.70.127:9000"
        MINIO_ACCESS_KEY = "minioadmin"
        MINIO_SECRET_KEY = "minioadmin"
        MINIO_BUCKET = "md-images"
        
        # 创建 MinIO 客户端
        client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        print(f"🔗 连接到 MinIO: {MINIO_ENDPOINT}")
        
        # 检查存储桶是否存在
        if client.bucket_exists(MINIO_BUCKET):
            print(f"✅ 存储桶 '{MINIO_BUCKET}' 已存在")
        else:
            print(f"📦 创建存储桶 '{MINIO_BUCKET}'")
            client.make_bucket(MINIO_BUCKET)
            print(f"✅ 存储桶 '{MINIO_BUCKET}' 创建成功")
        
        # 列出存储桶中的对象
        objects = list(client.list_objects(MINIO_BUCKET, recursive=True))
        print(f"📂 存储桶中有 {len(objects)} 个对象")
        
        if objects:
            print("前 5 个对象:")
            for i, obj in enumerate(objects[:5]):
                print(f"   {i+1}. {obj.object_name} ({obj.size} 字节)")
        
        return True
        
    except Exception as e:
        print(f"❌ MinIO 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 DoclingWordToMarkdownConverter + MinIO 测试")
    
    # 切换到测试目录
    os.chdir(Path(__file__).parent)
    
    # 测试 MinIO 连接
    print("\n" + "="*60)
    print("第一步：测试 MinIO 连接")
    print("="*60)
    
    minio_success = test_minio_connection()
    
    if minio_success:
        print("\n" + "="*60)
        print("第二步：测试完整的文档转换功能")
        print("="*60)
        test_with_real_minio()
    else:
        print("\n❌ MinIO 连接失败，跳过文档转换测试")
        print("💡 请检查 MinIO 服务是否正在运行，以及网络连接是否正常")
    
    print("\n🏁 测试完成")
