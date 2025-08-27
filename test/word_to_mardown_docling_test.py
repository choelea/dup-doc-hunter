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
    """主函数，用于命令行测试"""
    if len(sys.argv) != 3:
        print("用法: python word_to_mardown_docling_test.py <源文件路径> <目标文件路径>")
        print("示例: python word_to_mardown_docling_test.py input/sample.docx output/sample.md")
        sys.exit(1)
    
    source_file = sys.argv[1]
    target_file = sys.argv[2]
    
    success = convert_doc_to_markdown(source_file, target_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()