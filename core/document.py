import re
from dataclasses import dataclass
from typing import List

import jieba
from datasketch import MinHash


@dataclass
class Document:
    """
    表示一个文档对象，包含文档的基本信息和 MinHash 签名。

    Attributes:
        doc_id (int): 文档的唯一标识符。
        doc_name (str): 文档的名称。
        minhash_signature (bytes): 文档的 MinHash 签名，存储为字节数组。
        token_set (str): 文档的去重 token 集合，存储为字符串。
    """
    doc_id: int
    doc_name: str
    minhash_signature: bytes
    token_set: str

    @staticmethod
    def generate_minhash_signature(tokens: List[str], num_perm: int) -> bytes:
        """
        根据 token 列表生成 MinHash 签名。

        Args:
            tokens (List[str]): 文本分割后的 token 列表。
            num_perm (int): MinHash 的维度（哈希函数的数量）。

        Returns:
            bytes: 生成的 MinHash 签名，存储为字节数组。
        """
        m = MinHash(num_perm=num_perm)
        for token in tokens:
            m.update(token.lower().encode("utf8"))
        return m.hashvalues.astype('>u8').tobytes()

    @classmethod
    def from_text(cls, doc_id: int, doc_name: str, content: str, num_perm: int):
        """
        根据文本内容生成 Document 对象。

        Args:
            doc_id (int): 文档的唯一标识符。
            doc_name (str): 文档的名称。
            content (str): 文档的文本内容。
            num_perm (int): MinHash 的维度（哈希函数的数量）。

        Returns:
            Document: 包含生成的 MinHash 签名和 token 集合的文档对象。
        """
        tokens = cls.split(content)
        signature = cls.generate_minhash_signature(tokens, num_perm)
        token_str = " ".join(set(tokens))
        return cls(doc_id, doc_name, signature, token_str)

    @staticmethod
    def split(text: str) -> list:
        """
        分割文本为 token 列表。

        Args:
            text (str): 输入的文本内容。

        Returns:
            list: 分割后的 token 列表。
        """
        tokens = Document.split_sentences(text)
        return tokens

    @staticmethod
    def split_sentences(text: str) -> list:
        """
        按中英文句子分割文本，保留分隔符在句子末尾。

        Args:
            text (str): 输入的文本内容。

        Returns:
            list: 分割后的句子列表，去掉首尾空格和空字符串。
        """
        sentences = re.split(r'(?<=[。！？；：，,;:\s])', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def split_by_jieba(text: str) -> List[str]:
        """
        使用 jieba 对文本进行分词。

        Args:
            text (str): 输入的文本内容。

        Returns:
            List[str]: 分词后的 token 列表，去掉空字符串。
        """
        tokens = jieba.lcut(text)
        return [token.strip() for token in tokens if token.strip()]

    @staticmethod
    def split_by_jieba_v2(text: str) -> list:
        """
        清理 Markdown 内容并分词，支持中英文分句和分词。

        Args:
            text (str): 输入的 Markdown 文本内容。

        Returns:
            list: 分割后的 token 列表，用于 MinHash。
        """
        # 清理 Markdown 表格和格式
        lines = text.splitlines()
        out_lines = []
        table_sep_re = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$')
        for line in lines:
            if table_sep_re.match(line):
                continue
            if '|' in line and line.strip().startswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                cells = [c for c in cells if c]
                if cells:
                    out_lines.append(' '.join(cells))
                continue
            out_lines.append(line)
        text = '\n'.join(out_lines)

        # 清理 Markdown 其他内容
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)  # 图片
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # 链接
        text = re.sub(r'```.*?```', ' ', text, flags=re.S)  # 代码块
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.M)  # 列表标记
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.M)  # 有序列表
        text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.M)  # 标题
        text = re.sub(r'[`*_~>]+', ' ', text)  # 修饰符
        text = re.sub(r'[ \t]+', ' ', text)  # 空白规范化

        # 分句
        sentences = re.split(r'(?<=[。！？；：，,;:.!?])|\n+', text)
        sentences = [s.strip() for s in sentences if s and s.strip()]

        # 分词
        tokens = []
        try:
            import jieba
            use_jieba = True
        except Exception:
            use_jieba = False

        en_num_token_re = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+(?:\.\d+)?|[\u4e00-\u9fff]")
        han_re = re.compile(r'[\u4e00-\u9fff]')

        for s in sentences:
            if use_jieba and han_re.search(s):
                tokens.extend([t for t in jieba.lcut(s) if t.strip()])
            else:
                tokens.extend(en_num_token_re.findall(s))

        tokens = [t for t in tokens if t.strip()]
        return tokens