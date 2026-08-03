"""Run the shared K4 retrieval benchmark with three chunking strategies.

The hashing embedder is dependency-free and lexical. It is more meaningful than
the repository's random mock embedder for an offline, reproducible comparison.
Use the multilingual local embedder for the final demo when dependencies exist.
"""
from __future__ import annotations

import hashlib
import math
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import chunk_document, load_documents
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.store import EmbeddingStore


DATA_DIR = PROJECT_ROOT / "data/k4_ecommerce"
DIMENSIONS = 4096
OFFICIAL_DOC_IDS = {
    "shopee-returns-refund-policy",
    "shopee-shipping-policy",
    "shopee-freeship-conditions",
    "shopee-seller-listing-policy",
    "shopee-prohibited-products-policy",
}

BENCHMARKS = [
    {
        "query": "Người mua có thể yêu cầu trả hàng hoàn tiền trong những trường hợp nào?",
        "gold_doc": "shopee-returns-refund-policy",
        "gold_terms": ("không nhận được sản phẩm", "sản phẩm bị lỗi", "giao sai sản phẩm"),
    },
    {
        "query": "Thời hạn gửi yêu cầu trả hàng hoàn tiền là bao lâu?",
        "gold_doc": "shopee-returns-refund-policy",
        "gold_terms": ("15 ngày", "24 giờ"),
    },
    {
        "query": "Với đơn hàng COD hoặc chuyển khoản, người mua cần điều kiện gì để nhận hoàn tiền?",
        "gold_doc": "shopee-returns-refund-policy",
        "gold_terms": ("liên kết", "tài khoản ngân hàng", "shopeepay"),
    },
    {
        "query": "Người mua nên làm gì nếu bao bì gói hàng bị rách, móp méo, vỡ hoặc ướt?",
        "gold_doc": "shopee-shipping-policy",
        "gold_terms": ("từ chối nhận hàng",),
    },
    {
        "query": "Quy định đăng bán yêu cầu người bán cung cấp thông tin sản phẩm như thế nào?",
        "gold_doc": "shopee-seller-listing-policy",
        "gold_terms": ("thông tin chính xác", "tiêu đề", "mô tả"),
        "metadata_filter": {"customer_role": "seller"},
    },
]

STRATEGIES = {
    "FixedSizeChunker(size=500, overlap=100)": FixedSizeChunker(chunk_size=500, overlap=100),
    "SentenceChunker(max_sentences=3)": SentenceChunker(max_sentences_per_chunk=3),
    "RecursiveChunker(size=700)": RecursiveChunker(chunk_size=700),
}


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def hashing_embed(text: str) -> list[float]:
    """Create a normalized bag-of-words/character-ngram vector."""
    normalised = _normalise(text)
    words = re.findall(r"[a-z0-9]+", normalised)
    features = words + ["w:" + "_".join(words[i : i + 2]) for i in range(len(words) - 1)]
    compact = " ".join(words)
    features.extend("c:" + compact[i : i + 4] for i in range(max(0, len(compact) - 3)))

    vector = [0.0] * DIMENSIONS
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest, "big") % DIMENSIONS
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def is_relevant(result: dict, benchmark: dict) -> bool:
    stored_doc_id = str(result["metadata"].get("doc_id", ""))
    original_doc_id = stored_doc_id.split("::chunk_", 1)[0]
    if original_doc_id != benchmark["gold_doc"]:
        return False
    content = _normalise(result["content"])
    return any(_normalise(term) in content for term in benchmark["gold_terms"])


def main() -> int:
    print("# Group benchmark results\n")
    print("Embedder: dependency-free lexical hashing (word, bigram, character 4-gram)\n")
    for strategy_name, chunker in STRATEGIES.items():
        documents = [doc for doc in load_documents(DATA_DIR) if doc.id in OFFICIAL_DOC_IDS]
        chunks = [piece for doc in documents for piece in chunk_document(doc, chunker)]
        store = EmbeddingStore(collection_name="group_benchmark", embedding_fn=hashing_embed)
        store.add_documents(chunks)
        print(f"## {strategy_name} ({store.get_collection_size()} chunks)\n")
        total = 0
        for number, benchmark in enumerate(BENCHMARKS, start=1):
            results = store.search_with_filter(
                benchmark["query"], top_k=3, metadata_filter=benchmark.get("metadata_filter")
            )
            relevant_ranks = [rank for rank, result in enumerate(results, start=1) if is_relevant(result, benchmark)]
            score = 2 if relevant_ranks and relevant_ranks[0] == 1 else 1 if relevant_ranks else 0
            total += score
            ranks = ", ".join(map(str, relevant_ranks)) or "none"
            print(f"### Q{number}: score={score}/2, relevant_rank={ranks}")
            print(f"Query: {benchmark['query']}\n")
            for rank, result in enumerate(results, start=1):
                doc_id = result["metadata"].get("doc_id")
                chunk_index = result["metadata"].get("chunk_index")
                preview = " ".join(result["content"].split())[:220]
                print(f"{rank}. score={result['score']:.4f}; {doc_id}#chunk-{chunk_index}: {preview}")
            print()
        print(f"**Total: {total}/10**\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
