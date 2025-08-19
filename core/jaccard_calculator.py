import numpy as np
from core.document import Document


class JaccardCalculator:
    def __init__(self, num_perm=128):
        """
        初始化 JaccardCalculator
        :param num_perm: MinHash 的维度
        """
        self.num_perm = num_perm

    def calculate_jaccard_similarity(self, sig1: bytes, sig2: bytes) -> float:
        """
        计算两个 MinHash 签名的 Jaccard 相似度
        :param sig1: 第一个签名（bytes）
        :param sig2: 第二个签名（bytes）
        :return: Jaccard 相似度
        """
        sig1_array = np.frombuffer(sig1, dtype=np.uint64)
        sig2_array = np.frombuffer(sig2, dtype=np.uint64)
        intersection = np.intersect1d(sig1_array, sig2_array).size
        union = np.union1d(sig1_array, sig2_array).size
        return intersection / union

    def filter_by_jaccard_similarity(self, text_content: str, documents: list, threshold: float) -> list:
        """
        根据 Jaccard 相似度过滤文档
        :param text_content: 输入文本内容
        :param documents: 文档对象数组
        :param threshold: Jaccard 相似度阈值
        :return: 超过阈值的文档对象数组
        """
        # 生成输入文本的 MinHash 签名
        input_tokens = Document.split(text_content)
        input_signature = Document.generate_minhash_signature(input_tokens, self.num_perm)

        # 过滤文档
        filtered_documents = []
        for document in documents:
            similarity = self.calculate_jaccard_similarity(input_signature, document.minhash_signature)
            if similarity > threshold:
                filtered_documents.append(document)

        return filtered_documents
