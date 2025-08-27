#!/usr/bin/env python3
"""
测试 Docling 转换器的测试脚本
"""

import os
import tempfile
import unittest
from pathlib import Path
from word_to_mardown_docling_test import convert_doc_to_markdown


class TestDoclingConverter(unittest.TestCase):
    """Docling 转换器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(__file__).parent
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        
    def test_convert_existing_docx(self):
        """测试转换存在的 DOCX 文件"""
        source_file = self.input_dir / "sample.docx"
        target_file = self.output_dir / "test_sample.md"
        
        if source_file.exists():
            result = convert_doc_to_markdown(str(source_file), str(target_file))
            self.assertTrue(result, "转换应该成功")
            self.assertTrue(target_file.exists(), "目标文件应该被创建")
        else:
            self.skipTest(f"测试文件不存在: {source_file}")
    
    def test_convert_nonexistent_file(self):
        """测试转换不存在的文件"""
        source_file = "nonexistent.docx"
        target_file = self.output_dir / "test_nonexistent.md"
        
        result = convert_doc_to_markdown(source_file, str(target_file))
        self.assertFalse(result, "转换不存在的文件应该失败")
    
    def test_convert_with_temp_output(self):
        """测试使用临时输出目录"""
        source_file = self.input_dir / "sample.docx"
        
        if source_file.exists():
            with tempfile.TemporaryDirectory() as temp_dir:
                target_file = Path(temp_dir) / "temp_output.md"
                result = convert_doc_to_markdown(str(source_file), str(target_file))
                self.assertTrue(result, "转换应该成功")
                self.assertTrue(target_file.exists(), "临时目标文件应该被创建")
        else:
            self.skipTest(f"测试文件不存在: {source_file}")


def run_manual_test():
    """手动测试函数"""
    print("=" * 50)
    print("手动测试 Docling 转换器")
    print("=" * 50)
    
    test_dir = Path(__file__).parent
    input_dir = test_dir / "input"
    output_dir = test_dir / "output"
    
    # 列出可用的测试文件
    docx_files = list(input_dir.glob("*.docx"))
    
    if not docx_files:
        print("❌ 在 input 目录中没有找到 .docx 文件")
        return
    
    print(f"📁 找到 {len(docx_files)} 个 DOCX 文件:")
    for i, file in enumerate(docx_files, 1):
        print(f"  {i}. {file.name}")
    
    # 测试每个文件
    for docx_file in docx_files:
        source_file = str(docx_file)
        target_file = str(output_dir / f"test_{docx_file.stem}.md")
        
        print(f"\n🔄 测试转换: {docx_file.name}")
        success = convert_doc_to_markdown(source_file, target_file)
        
        if success:
            print(f"✅ 成功: {target_file}")
        else:
            print(f"❌ 失败: {docx_file.name}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        run_manual_test()
    else:
        unittest.main()
