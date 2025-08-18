import os
import time
from core.document import Document
from core.markdown_file_processor import MarkdownFileProcessor
from core.milvus_minhash_lsh_service import MilvusMinHashLSHService

if __name__ == "__main__":
    """
    将指定的文件夹下面的 markdown 进行内容指纹的计算，并存储只 milvus 数据库
    """
    md_folder_path = "/Users/joe/Downloads/dup_doc_test/markdown"
    # md_folder_path = "/Users/joe/codes/michael/mddoc_variants_generator/md_doc_7"
    source_file = ("/Users/joe/Downloads/dup_doc_test/target.md")
    COLLECTION_NAME = "few_shot_test"

    # 记录开始时间，运行完成后记录个时间，算运行耗时
    start_time = time.time()
    print(f"开始处理时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")


    markdown_sentence_splitter = MarkdownFileProcessor()
    # 初始化 Milvus 服务
    service = MilvusMinHashLSHService(
        uri="http://10.3.70.127:19530",
        collection_name=COLLECTION_NAME
    )
    # service.drop_collection()
    service.create_collection()
    # 1. 从一个指定的文件夹路径 md_folder_path 下读取所有.md结尾的文件，读取文件的到文本 text;
    markdown_files = [f for f in os.listdir(md_folder_path) if f.endswith('.md')]

    if not markdown_files:
        print(f"目录 '{md_folder_path}' 中未找到 Markdown 文件")
    else:
        print(f"找到 {len(markdown_files)} 个 Markdown 文件")
    documents = []
    for i, md_file in enumerate(markdown_files):
        file_path = os.path.join(md_folder_path, md_file)
        print(f"\n处理文件: {md_file}")
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            content = markdown_sentence_splitter.markdown_to_text(markdown_text)
            document = Document.from_text(
                doc_id=i,
                doc_name=md_file,
                content=content,
                num_perm=service.MINHASH_DIM
            )
            documents.append(document)
    service.insert_documents(documents)

    print("------------------ search testing -------------------------------")
    with open(source_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
        content = markdown_sentence_splitter.markdown_to_text(markdown_text)
        queryDocument = Document.from_text(
            doc_id=0,
            doc_name=source_file,
            content=content,
            num_perm=service.MINHASH_DIM
        )

        # 调用milvus_service.search_similar进行相似文档检索并打印出来
        results = service.search(queryDocument.minhash_signature, 8, 16)
        for idx, r in enumerate(results, start=1):
            print(
                f"{idx}. Similarity: {r['similarity']:.3f} "
                f"| distance: {r['distance']:.3f}"
                f"| doc_id: {r['doc_id']} "
                f"| doc_name: {r['doc_name']} "
            )

    end_time = time.time()
    print(f"结束处理时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"总耗时: {end_time - start_time:.2f} 秒")
