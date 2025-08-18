from core.document import Document
from core.milvus_minhash_lsh_service import MilvusMinHashLSHService

if __name__ == "__main__":
    # 初始化 Milvus 服务
    service = MilvusMinHashLSHService(
        uri="http://10.3.70.127:19530",
        collection_name="text_test"
    )
    service.drop_collection()
    service.create_collection()

    # 文档列表
    docs_data = [
        {"name": "doc1", "content": "The quick brown fox jumps over the lazy dog"},
        {"name": "doc2", "content": "A quick brown fox jumps over the lazy dog"},
        {"name": "doc3", "content": "Completely unrelated text about machine learning and AI"},
        {"name": "doc4", "content": "The quick brown fox leaps over a sleepy dog"}
    ]

    query = "The quick brown fox jumps over the lazy dog"

    # 使用 Document.from_text 生成 Document 对象，并插入
    documents = []
    for i, doc in enumerate(docs_data):
        document = Document.from_text(
            doc_id=i,
            doc_name=doc["name"],
            content=doc["content"],
            num_perm=service.MINHASH_DIM
        )
        documents.append(document)

    # 插入 Milvus
    service.insert_documents(documents)

    # 搜索
    queryDoc = Document.from_text(1, "test", query, service.MINHASH_DIM)
    results = service.search(queryDoc.minhash_signature, 6, 12)
    for idx, r in enumerate(results, start=1):
        print(
            f"{idx}. Similarity: {r['similarity']:.3f} "
            f"| doc_id: {r['doc_id']} "
            f"| doc_name: {r['doc_name']} "
            f"| token_set: {r['token_set']}"
        )
