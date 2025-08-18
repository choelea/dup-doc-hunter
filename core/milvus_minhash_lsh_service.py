import re
from typing import List
from pymilvus import MilvusClient, DataType

from core.document import Document


class MilvusMinHashLSHService:
    """
    基于 Milvus + MinHash LSH 的文本相似度搜索服务。

    - 支持文档的 MinHash 签名存储与检索
    - 支持 Jaccard 相似度计算
    - 适合做文本去重、近似匹配、相似文档检索
    """
    def __init__(self, uri: str, collection_name: str, minhash_dim=256, hash_bit_width=64):
        """
        初始化服务。

        :param uri: Milvus 服务地址，例如 "http://127.0.0.1:19530"
        :param collection_name: 集合名称
        :param minhash_dim: MinHash 的签名长度（哈希值数量）
        :param hash_bit_width: 每个哈希值的 bit 宽度（通常 64）
        """
        self.client = MilvusClient(uri=uri)
        self.collection_name = collection_name
        self.MINHASH_DIM = minhash_dim
        self.HASH_BIT_WIDTH = hash_bit_width
        # BINARY_VECTOR 的维度 = 哈希值数量 × 每个哈希值的 bit 数
        self.VECTOR_DIM = self.MINHASH_DIM * self.HASH_BIT_WIDTH

    def drop_collection(self):
        """
        删除 Milvus 集合（如果存在）。
        """
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' dropped.")
        else:
            print(f"Collection '{self.collection_name}' does not exist.")

    def create_collection(self):
        """
        创建 Milvus 集合 schema 和索引。
        包含字段：
        - doc_id: 主键，文档 ID
        - doc_name: 文档名称
        - minhash_signature: MinHash 签名（二进制向量）
        - token_set: 文档的去重 token 集合（字符串表示）
        """
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("doc_id", DataType.INT64, is_primary=True)
        schema.add_field("doc_name", DataType.VARCHAR, max_length=1000)
        schema.add_field("minhash_signature", DataType.BINARY_VECTOR, dim=self.VECTOR_DIM)
        # token_set 存全文 token，max_length 65535 足够容纳较大文本
        schema.add_field("token_set", DataType.VARCHAR, max_length=65535)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="minhash_signature",
            index_type="MINHASH_LSH",
            metric_type="MHJACCARD",
            params={
                "mh_element_bit_width": self.HASH_BIT_WIDTH,
                "mh_lsh_band": 16,
                "with_raw_data": True
            }
        )

        self.client.create_collection(self.collection_name, schema=schema, index_params=index_params)

    def insert_documents(self, docs: list[Document]):
        """
        批量插入文档到 Milvus。

        :param docs: Document 对象列表
        """
        insert_data = []
        for document in docs:
            insert_data.append({
                "doc_id": document.doc_id,
                "doc_name": document.doc_name,
                "minhash_signature": document.minhash_signature,
                "token_set": document.token_set
            })
        self.client.insert(self.collection_name, insert_data)
        self.client.flush(self.collection_name)

    def search(self, query_sig: bytes, top_k=3, refine_k=6):
        """
        基于 MinHash 签名搜索相似文档，并按相似度降序排序。

        :param query_sig: 查询文本的 MinHash 签名（二进制向量）
        :param top_k: 返回的相似文档数量
        :param refine_k: LSH 近似搜索的候选数量（越大结果越准，速度稍慢）
        :return: 按相似度排序的搜索结果列表
        """
        search_params = {
            "metric_type": "MHJACCARD",
            "params": {
                "mh_search_with_jaccard": True,
                "refine_k": refine_k
            }
        }

        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_sig],
            anns_field="minhash_signature",
            search_params=search_params,
            limit=top_k,
            output_fields=["doc_id", "doc_name", "token_set"],
            consistency_level="Bounded"
        )

        output = []
        for hit in results[0]:
            similarity = hit['distance']  # Jaccard 相似度 = 1 - distance
            output.append({
                "similarity": round(similarity, 3),
                "distance": hit['distance'],
                "doc_id": hit['entity']['doc_id'],
                "doc_name": hit['entity']['doc_name'],
                "token_set": hit['entity']['token_set']
            })

        # 按相似度从高到低排序
        output.sort(key=lambda x: x["similarity"], reverse=True)
        return output