import re
from pathlib import Path
from markdown_it import MarkdownIt


class MarkdownFileProcessor:
    def __init__(self):
        """初始化 Markdown 解析器"""
        self.md = MarkdownIt()

    def markdown_to_text(self, md_text: str) -> str:
        """解析 Markdown 为纯文本"""
        tokens = self.md.parse(md_text)
        text_parts = []
        for token in tokens:
            if token.type == "inline":
                text_parts.append(token.content)
        return "\n".join(text_parts)

    def process_file(self, file_path: Path) -> list:
        """读取并处理单个 Markdown 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        plain_text = self.markdown_to_text(md_text)
        return self.split_sentences(plain_text)

    def process_directory(self, dir_path: Path) -> dict:
        """
        批量处理目录下的 Markdown 文件
        返回 {文件名: [短句列表]} 字典
        """
        results = {}
        for file_path in Path(dir_path).rglob("*.md"):
            results[file_path.name] = self.process_file(file_path)
        return results
