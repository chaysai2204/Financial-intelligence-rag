import os
import sys

from dotenv import load_dotenv

from llm.azure_openai import get_embedding_client
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    Retriever,
    DenseRetriever,
)


load_dotenv()


def get_vector_store():
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

    if not endpoint or not api_key or not index_name:
        raise RuntimeError(
            "Missing Azure Search configuration. "
            "Check AZURE_SEARCH_ENDPOINT, "
            "AZURE_SEARCH_API_KEY, and "
            "AZURE_SEARCH_INDEX_NAME."
        )

    return AzureAISearchVectorStore(
        endpoint=endpoint,
        api_key=api_key,
        index_name=index_name,
    )


def search(
    query: str,
    strategy: str,
    top_k: int = 5,
):
    store = get_vector_store()

    if strategy == "bm25":
        retriever = Retriever(store.client)

    elif strategy == "dense":
        embeddings = get_embedding_client()

        retriever = DenseRetriever(
            client=store.client,
            embeddings=embeddings,
        )

    else:
        raise ValueError(
            "Strategy must be either 'bm25' or 'dense'."
        )

    documents = retriever.invoke(
        query=query,
        top_k=top_k,
    )

    print(f"Strategy: {strategy.upper()}")
    print(f"Query: {query!r}")
    print(f"Top K: {top_k}")
    print(f"Results: {len(documents)}\n")

    for doc in documents:
        metadata = doc.metadata

        snippet = doc.page_content.strip().replace("\n", " ")

        if len(snippet) > 350:
            snippet = snippet[:350].rstrip() + "..."

        print(f"Rank: {metadata['rank']}")
        print(f"Score: {metadata['score']}")
        print(f"Chunk ID: {metadata['chunk_id']}")
        print(f"Document ID: {metadata['document_id']}")
        print(f"Company: {metadata['company']}")
        print(f"Ticker: {metadata['ticker']}")
        print(f"Year: {metadata['year']}")
        print(f"Chunk index: {metadata['chunk_index']}")
        print(f"Source: {metadata['source_file']}")
        print(f"Content: {snippet}")
        print("-" * 80)

    if not documents:
        print("No results returned.")

    return documents


def main():
    if len(sys.argv) < 3:
        print(
            "Usage:\n"
            '  python -m rag.retrieval_debug bm25 "your query"\n'
            '  python -m rag.retrieval_debug dense "your query"'
        )
        sys.exit(1)

    strategy = sys.argv[1].lower()
    query = " ".join(sys.argv[2:])

    search(
        query=query,
        strategy=strategy,
    )


if __name__ == "__main__":
    main()