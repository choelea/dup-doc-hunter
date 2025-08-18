import re
from markdown_it import MarkdownIt
from pathlib import Path


def markdown_to_text(md_text: str) -> str:
    """解析 Markdown 为纯文本"""
    md = MarkdownIt()
    tokens = md.parse(md_text)
    text_parts = []
    for token in tokens:
        if token.type == "inline":
            text_parts.append(token.content)
    return "\n".join(text_parts)


def split_sentences(text: str) -> list:
    """
    按中英文句子分割，同时把逗号、冒号、分号也算作分隔符
    保留分隔符在句子末尾
    """
    # 匹配中文句号、问号、感叹号、逗号、冒号、分号
    # 以及英文 .,?!:;
    sentences = re.split(r'(?<=[。！？；：，,;:|])', text)
    return [s.strip() for s in sentences if s and s.strip()]


def process_markdown_file(file_path: Path) -> list:
    """读取并处理一个 Markdown 文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    plain_text = markdown_to_text(md_text)
    return split_sentences(plain_text)


def main():
    md_file = Path("example.md")

    if not md_file.exists():
        print(f"文件不存在: {md_file}")
        return

    sentences = process_markdown_file(md_file)

    print(f"共提取 {len(sentences)} 条短句：")
    for idx, s in enumerate(sentences, 1):
        print(f"{idx}: {s}")


if __name__ == "__main__":
    main()