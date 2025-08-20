import os
import numpy as np
from core.document import Document
from core.markdown_file_processor import MarkdownFileProcessor


def calculate_jaccard_similarity(sig1, sig2):
    """
    计算两个 MinHash 签名的 Jaccard 相似度。
    :param sig1: 第一个签名（NumPy 数组）
    :param sig2: 第二个签名（NumPy 数组）
    :return: Jaccard 相似度
    """
    intersection = np.intersect1d(sig1, sig2).size
    union = np.union1d(sig1, sig2).size
    return intersection / union


def test_directory_similarity(md_folder_path, threshold=0.5):
    """
    测试目录中每个文件的相似度，输出超过阈值的相似文档。
    :param md_folder_path: Markdown 文件所在目录
    :param threshold: Jaccard 相似度阈值
    """
    markdown_sentence_splitter = MarkdownFileProcessor()

    # 读取目录中的 Markdown 文件
    markdown_files = [f for f in os.listdir(md_folder_path) if f.endswith('.md')]
    if not markdown_files:
        print(f"目录 '{md_folder_path}' 中未找到 Markdown 文件")
        return

    print(f"找到 {len(markdown_files)} 个 Markdown 文件")

    # 生成每个文件的 MinHash 签名
    documents = []
    for i, md_file in enumerate(markdown_files):
        file_path = os.path.join(md_folder_path, md_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            content = markdown_sentence_splitter.markdown_to_text(markdown_text)
            document = Document.from_text(
                doc_id=i,
                doc_name=md_file,
                content=content,
                num_perm=128  # 假设 MinHash 的维度为 128
            )
            documents.append(document)

    # 计算两两文件的相似度
    results = {}
    for i, doc1 in enumerate(documents):
        doc1_sig_array = np.frombuffer(doc1.minhash_signature, dtype=np.uint64)
        similar_docs = []
        for j in range(i + 1, len(documents)):  # 避免重复对比
            doc2 = documents[j]
            doc2_sig_array = np.frombuffer(doc2.minhash_signature, dtype=np.uint64)
            similarity = calculate_jaccard_similarity(doc1_sig_array, doc2_sig_array)
            if similarity > threshold:
                similar_docs.append((doc2.doc_name, round(similarity, 3)))

        if similar_docs:
            results[doc1.doc_name] = similar_docs

    # 输出结果
    print("------------------ 目录文件相似度测试结果 -------------------------------")
    for doc_name, similar_docs in results.items():
        similar_doc_names = [f"{idx + 1}、{name} (相似度: {sim})" for idx, (name, sim) in enumerate(similar_docs)]
        print(f"{doc_name}：相似文档：{'，'.join(similar_doc_names)}")


if __name__ == "__main__":
    md_folder_path = "/Users/joe/Downloads/dup_doc_test/markdown"  # 替换为你的目录路径
    similarity_threshold = 0.2  # 设置相似度阈值
    test_directory_similarity(md_folder_path, similarity_threshold)