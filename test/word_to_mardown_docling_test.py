import os
import sys
from pathlib import Path
from docling.document_converter import DocumentConverter


def convert_doc_to_markdown(source_file: str, target_file: str) -> bool:
    """
    将文档文件转换为 Markdown 格式
    
    Args:
        source_file (str): 源文件路径，支持 .doc, .docx, .html, .pdf 等格式
        target_file (str): 目标 Markdown 文件路径
        
    Returns:
        bool: 转换成功返回 True，失败返回 False
        
    Raises:
        FileNotFoundError: 源文件不存在
        ValueError: 文件路径无效
        Exception: 转换过程中发生错误
    """
    try:
        # 验证源文件是否存在
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"源文件不存在: {source_file}")
            
        # 验证源文件路径
        source_path = Path(source_file)
        if not source_path.is_file():
            raise ValueError(f"源路径不是有效文件: {source_file}")
            
        # 创建目标文件目录（如果不存在）
        target_path = Path(target_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Docling 转换器
        converter = DocumentConverter()
        
        print(f"🔄 开始转换文件: {source_file}")
        
        # 转换为 Docling 的 Document 对象
        result = converter.convert(source_file)
        doc = result.document
        
        # 导出为 Markdown（表格会变成 pipe table）
        markdown_text = doc.export_to_markdown()
        
        # 保存为 .md 文件
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
        print(f"✅ 转换完成，已生成 Markdown 文件: {target_file}")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        return False
    except ValueError as e:
        print(f"❌ 参数错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False


def main():
    """主函数，测试 input 目录下的所有 Word 文档"""
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent
    input_dir = script_dir / "input"
    output_dir = script_dir / "output"
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)
    
    # 查找所有 Word 文档
    word_files = list(input_dir.glob("*.docx")) + list(input_dir.glob("*.doc"))
    
    if not word_files:
        print("❌ 在 input 目录中没有找到 Word 文档")
        sys.exit(1)
    
    print(f"🚀 开始测试 {len(word_files)} 个 Word 文档的转换")
    print("=" * 60)
    
    success_count = 0
    total_count = len(word_files)
    
    for word_file in word_files:
        print(f"\n📄 处理文档: {word_file.name}")
        
        # 生成对应的 Markdown 文件名
        md_filename = word_file.stem + ".md"
        target_file = output_dir / md_filename
        
        # 转换文档
        success = convert_doc_to_markdown(str(word_file), str(target_file))
        
        if success:
            success_count += 1
            print(f"✅ 成功转换: {word_file.name} -> {md_filename}")
        else:
            print(f"❌ 转换失败: {word_file.name}")
    
    print("\n" + "=" * 60)
    print(f"📊 转换完成统计:")
    print(f"   总计: {total_count} 个文档")
    print(f"   成功: {success_count} 个")
    print(f"   失败: {total_count - success_count} 个")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有文档转换成功!")
        sys.exit(0)
    else:
        print("⚠️ 部分文档转换失败")
        sys.exit(1)


if __name__ == "__main__":
    main()