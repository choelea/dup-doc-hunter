import re
from dataclasses import dataclass
from typing import List

import jieba
from datasketch import MinHash


@dataclass
class Document:
    doc_id: int
    doc_name: str
    minhash_signature: bytes
    token_set: str

    @staticmethod
    def generate_minhash_signature(tokens: List[str], num_perm: int) -> bytes:
        """生成 MinHash 签名，入参为 token 数组"""
        m = MinHash(num_perm=num_perm)
        for token in tokens:
            m.update(token.lower().encode("utf8"))
        return m.hashvalues.astype('>u8').tobytes()

    @classmethod
    def from_text(cls, doc_id: int, doc_name: str, content: str, num_perm: int):
        """根据 文本内容 content生成 Document 对象"""
        tokens = cls.split(content)
        signature = cls.generate_minhash_signature(tokens, num_perm)
        token_str = " ".join(set(tokens))
        return cls(doc_id, doc_name, signature, token_str)

    @staticmethod
    def split(text: str) -> list:
        """
        分割文本为 token 列表
        """
        # tokens = Document.split_sentences(text)
        # tokens = Document.split_by_jieba(text)
        tokens = Document.split_by_jieba_v2(text)
        return tokens

    @staticmethod
    def split_sentences(text: str) -> list:
        """
        按中英文句子分割，包含空格、逗号、冒号、分号
        保留分隔符在句子末尾，去掉句末多余空格
        """
        # \s 代表空白字符，加入到分隔符集合中
        sentences = re.split(r'(?<=[。！？；：，,;:\s])', text)
        # sentences = re.split(r'(?<=[。\s])', text)
        # 去掉句子首尾的空格，并过滤掉空字符串
        return [s.strip() for s in sentences if s.strip()]

    def split_by_jieba(text: str) -> List[str]:
        """
        使用 jieba 对文本进行分词，并返回分词结果
        """
        tokens = jieba.lcut(text)
        return [token.strip() for token in tokens if token.strip()]

    @staticmethod
    def split_by_jieba_v2(text: str) -> list:
        """
        清理 Markdown（保留表格内容）、按中英文标点/换行分句，
        中文优先用 jieba 分词，英文按单词/数字切分。
        返回 token 列表（用于 MinHash）。
        """
        # --- 0) 先把 Markdown 表格“转写”为普通文本：保留单元格内容，去掉 | 和分隔线 ---
        lines = text.splitlines()
        out_lines = []
        # 表头分隔线，如: | --- | :---: | ---: |
        table_sep_re = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$')
        for line in lines:
            # 跳过纯表格分隔线
            if table_sep_re.match(line):
                continue
            if '|' in line and line.strip().startswith('|'):
                # 表格内容行：拆单元格，保留文字
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                cells = [c for c in cells if c]  # 去掉空单元格
                if cells:
                    out_lines.append(' '.join(cells))
                continue
            out_lines.append(line)
        text = '\n'.join(out_lines)

        # --- 1) 其它 Markdown 清洗：保留可读内容 ---
        # 图片：保留 alt 文本
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
        # 链接：保留可见文本
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 代码块（fenced code）整体移除，避免大量噪声
        text = re.sub(r'```.*?```', ' ', text, flags=re.S)
        # 行级列表标记与标题符号去掉
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.M)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.M)
        text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.M)
        # 强调/行内代码等修饰符去掉
        text = re.sub(r'[`*_~>]+', ' ', text)
        # 规范空白
        text = re.sub(r'[ \t]+', ' ', text)

        # --- 2) 分句：按中英文标点或换行 ---
        sentences = re.split(r'(?<=[。！？；：，,;:.!?])|\n+', text)
        sentences = [s.strip() for s in sentences if s and s.strip()]
        # --- 3) 分词：中文用 jieba（若可用），英文/数字用正则 ---
        tokens = []
        try:
            import jieba  # 可选依赖
            use_jieba = True
        except Exception:
            use_jieba = False

        en_num_token_re = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+(?:\.\d+)?|[\u4e00-\u9fff]")
        han_re = re.compile(r'[\u4e00-\u9fff]')

        for s in sentences:
            if use_jieba and han_re.search(s):
                # 中文优先用 jieba 切
                tokens.extend([t for t in jieba.lcut(s) if t.strip()])
            else:
                # 回退：英文单词/数字 + 单个汉字
                tokens.extend(en_num_token_re.findall(s))

        # 可选：去掉非常短的噪声 token
        tokens = [t for t in tokens if t.strip()]

        return tokens