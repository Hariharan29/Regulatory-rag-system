"""Print dense, BM25, and fused results for a small query set."""

from app.core.database import create_session
from app.services.dense_retrieval import dense_search
from app.services.hybrid_retrieval import reciprocal_rank_fusion
from app.services.sparse_retrieval import BM25Retriever

SAMPLE_QUERIES = [
    "What are the KYC norms for NBFCs?",
    "Requirements for reporting cyber security incidents",
    "How should regulated entities classify non-performing assets?",
    "Rules for customer grievance redressal",
    "Disclosure requirements for investment advisers",
]


def print_results(label, results) -> None:
    print(f"\n{label}")
    for result in results:
        chunk = result.chunk
        excerpt = chunk.content[:240].replace("\n", " ")
        print(
            f"  score={result.score:.5f} | {chunk.document.title} "
            f"(page {chunk.page_number}) | {excerpt}"
        )


def main() -> None:
    db = create_session()
    try:
        sparse_retriever = BM25Retriever.from_session(db)
        for query in SAMPLE_QUERIES:
            dense = dense_search(db, query, top_k=5)
            sparse = sparse_retriever.search(query, top_k=5)
            hybrid = reciprocal_rank_fusion(dense, sparse, top_k=5)
            print(f"\nQuery: {query}")
            print_results("Dense", dense)
            print_results("BM25", sparse)
            print_results("Hybrid RRF", hybrid)
    finally:
        db.close()


if __name__ == "__main__":
    main()
