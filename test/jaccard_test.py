import os
import time
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


if __name__ == "__main__":
    start_time = time.time()  # 记录开始时间
    print(f"开始处理时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    md_folder_path = "/Users/joe/Downloads/dup_doc_test/markdown"
    source_file = "/Users/joe/Downloads/dup_doc_test/target.md"

    markdown_sentence_splitter = MarkdownFileProcessor()

    # 读取目标文件并生成 MinHash 签名
    with open(source_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
        content = markdown_sentence_splitter.markdown_to_text(markdown_text)
        query_document = Document.from_text(
            doc_id=0,
            doc_name=source_file,
            content=content,
            num_perm=128  # 假设 MinHash 的维度为 128
        )
    query_sig_array = np.frombuffer(query_document.minhash_signature, dtype=np.uint64)

    # 读取文件夹中的 Markdown 文件并计算相似度
    markdown_files = [f for f in os.listdir(md_folder_path) if f.endswith('.md')]
    if not markdown_files:
        print(f"目录 '{md_folder_path}' 中未找到 Markdown 文件")
    else:
        print(f"找到 {len(markdown_files)} 个 Markdown 文件")

    results = []
    for i, md_file in enumerate(markdown_files):
        file_path = os.path.join(md_folder_path, md_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            content = markdown_sentence_splitter.markdown_to_text(markdown_text)
            document = Document.from_text(
                doc_id=i,
                doc_name=md_file,
                content=content,
                num_perm=128
            )
            candidate_sig_array = np.frombuffer(document.minhash_signature, dtype=np.uint64)
            jaccard_similarity = calculate_jaccard_similarity(query_sig_array, candidate_sig_array)
            results.append({
                "doc_id": i,
                "doc_name": md_file,
                "similarity": round(jaccard_similarity, 3)
            })

    # 按相似度从高到低排序并打印结果
    results.sort(key=lambda x: x["similarity"], reverse=True)
    print("------------------ 手动计算 Jaccard 相似度结果 -------------------------------")
    for idx, result in enumerate(results, start=1):
        print(
            f"{idx}. Similarity: {result['similarity']:.3f} | doc_id: {result['doc_id']} | doc_name: {result['doc_name']}")

    end_time = time.time()  # 记录结束时间
    print(f"结束处理时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"总耗时: {end_time - start_time:.2f} 秒")