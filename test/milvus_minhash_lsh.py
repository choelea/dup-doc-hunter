from datasketch import MinHash
from pymilvus import MilvusClient

from pymilvus import DataType

client = MilvusClient(uri="http://10.3.70.127:19530")  # Update if your URI is different


MINHASH_DIM = 256
HASH_BIT_WIDTH = 64

def generate_minhash_signature(text, num_perm=MINHASH_DIM) -> bytes:
    m = MinHash(num_perm=num_perm)
    for token in text.lower().split():
        m.update(token.encode("utf8"))
    return m.hashvalues.astype('>u8').tobytes()  # Returns 2048 bytes

def extract_token_set(text: str) -> str:
    tokens = set(text.lower().split())
    return " ".join(tokens)


if __name__ == "__main__":

    VECTOR_DIM = MINHASH_DIM * HASH_BIT_WIDTH  # 256 × 64 = 8192 bits

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("doc_id", DataType.INT64, is_primary=True)
    schema.add_field("minhash_signature", DataType.BINARY_VECTOR, dim=VECTOR_DIM)
    schema.add_field("token_set", DataType.VARCHAR, max_length=1000)  # required for refinement
    schema.add_field("document", DataType.VARCHAR, max_length=1000)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="minhash_signature",
        index_type="MINHASH_LSH",
        metric_type="MHJACCARD",
        params={
            "mh_element_bit_width": HASH_BIT_WIDTH,  # Must match signature bit width
            "mh_lsh_band": 64,                       # Band count (128/16 = 8 hashes per band)
            "with_raw_data": True                    # Required for Jaccard refinement
        }
    )

    client.create_collection("minhash_demo", schema=schema, index_params=index_params)


    documents = [
        "The quick brown fox jumps over the lazy dog",
        "A quick brown fox jumps over the lazy dog",
        "Completely unrelated text about machine learning and AI",
        "The quick brown fox leaps over a sleepy dog"
    ]

    insert_data = []
    for i, doc in enumerate(documents):
        sig = generate_minhash_signature(doc)
        token_str = extract_token_set(doc)
        insert_data.append({
            "doc_id": i,
            "minhash_signature": sig,
            "token_set": token_str,
            "document": doc
        })

    client.insert("minhash_demo", insert_data)
    client.flush("minhash_demo")


    # query_text = "neural networks model patterns in data"
    query_text = "The quick brown fox jumps over the lazy dog"
    query_sig = generate_minhash_signature(query_text)

    search_params = {
        "metric_type": "MHJACCARD",
        "params": {
            "mh_search_with_jaccard": True,  # Enable real Jaccard computation
            "refine_k": 12  # Refine top 5 candidates
        }
    }

    refined_results = client.search(
        collection_name="minhash_demo",
        data=[query_sig],
        anns_field="minhash_signature",
        # highlight-next-line
        search_params=search_params,
        limit=6,
        output_fields=["doc_id", "document"],
        consistency_level="Bounded"
    )

    for i, hit in enumerate(refined_results[0]):
        sim = 1 - hit['distance']
        print(f"{i + 1}. Similarity: {sim:.3f} | {hit['entity']['document']}")


# 输出结果类似如下
"""
Query: The quick brown fox jumps over the lazy dog
1. Similarity: 0.047 | A quick brown fox jumps over the lazy dog
2. Similarity: 0.211 | The quick brown fox leaps over a sleepy dog
3. Similarity: 0.495 | Completely unrelated text about machine learning and AI
4. Similarity: 0.000 | The quick brown fox jumps over the lazy dog
"""