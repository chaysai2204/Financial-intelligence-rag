import hashlib

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from types import SimpleNamespace
def build_filter(
    company: str | None = None,
    year: int | str | None = None,
    document_id: str | None = None,
) -> str | None:
    """
    Build an Azure AI Search OData filter
    from optional document metadata.
    """
    filters = []

    if company:
        filters.append(
            f"company eq '{company}'"
        )

    if year:
        filters.append(
            f"year eq '{year}'"
        )

    if document_id:
        filters.append(
            f"document_id eq '{document_id}'"
        )

    if not filters:
        return None

    return " and ".join(filters)


class AzureAISearchVectorStore:
    """Azure AI Search vector store."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str
    ) -> None:

        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )


    def upload_chunks(
        self,
        chunks,
        embeddings,
        document_id: str,
        company: str,
        ticker: str,
        year: str,
        filing_type: str,
        source_file: str,
        file_hash: str
    ) -> None:
        """
        Upload chunks with provenance metadata
        using deterministic chunk IDs.
        """

        documents = []

        texts = [chunk.page_content for chunk in chunks]

        vectors = embeddings.embed_documents(texts)

        for chunk_index, (chunk, vector) in enumerate(
            zip(chunks, vectors)
        ):
            chunk_id = hashlib.sha256(
                f"{file_hash}:{chunk_index}".encode("utf-8")
            ).hexdigest()

            documents.append(
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "company": company,
                    "ticker": ticker,
                    "year": year,
                    "filing_type": filing_type,
                    "source_file": source_file,
                    "file_hash": file_hash,
                    "chunk_index": chunk_index,
                    "content": chunk.page_content,
                    "content_vector": vector
                }
            )

        result = self.client.upload_documents(documents)

        uploaded = sum(
            item.succeeded
            for item in result
        )

        print(
            f"Uploaded {uploaded}/{len(documents)} chunks."
        )


class Retriever:
    """
    Simple Azure Search lexical retriever.

    This remains our BM25 baseline for now.
    """

    def __init__(self, client):
        self.client = client

    def invoke(
        self,
        query: str,
        company: str | None = None,
        year: int | str | None = None,
        document_id: str | None = None,
        top_k: int = 20
    ) -> list:
        filter_expr = build_filter(
           company=company,
           year=year,
           document_id=document_id,
        )
       
        results = (
            self.client.search(
                search_text=query,
                top=top_k,
                filter=filter_expr
            )
            if filter_expr
            else self.client.search(
                search_text=query,
                top=top_k
            )
        )

        documents = []

        for rank, result in enumerate(results, start=1):
            content = result.get("content", "")

            documents.append(
                SimpleNamespace(
                    page_content=content,
                    metadata={
                        "rank": rank,
                        "score": result.get("@search.score"),
                        "chunk_id": result.get("id"),
                        "document_id": result.get("document_id"),
                        "chunk_index": result.get("chunk_index"),
                        "company": result.get("company"),
                        "ticker": result.get("ticker"),
                        "year": result.get("year"),
                        "filing_type": result.get("filing_type"),
                        "source_file": result.get("source_file"),
                        "file_hash": result.get("file_hash"),
                    }
                )
            )

        return documents

class DenseRetriever:
    """
    Azure AI Search dense vector retriever.

    Uses a query embedding to search against
    the stored content_vector field.
    """

    def __init__(self, client, embeddings):
        self.client = client
        self.embeddings = embeddings

    def invoke(
        self,
        query: str,
        company: str | None = None,
        year: int | str | None = None,
        document_id: str | None = None,
        top_k: int = 20
    ) -> list:
        filter_expr = build_filter(
           company=company,
           year=year,
           document_id=document_id,
        )
       
        query_vector = self.embeddings.embed_query(query)

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )

        results = self.client.search(
            search_text=None,
            vector_queries=[vector_query],
            top=top_k,
            filter=filter_expr,
        )

        documents = []

        for rank, result in enumerate(results, start=1):
            content = result.get("content", "")

            documents.append(
                SimpleNamespace(
                    page_content=content,
                    metadata={
                        "rank": rank,
                        "score": result.get("@search.score"),
                        "chunk_id": result.get("id"),
                        "document_id": result.get("document_id"),
                        "chunk_index": result.get("chunk_index"),
                        "company": result.get("company"),
                        "ticker": result.get("ticker"),
                        "year": result.get("year"),
                        "filing_type": result.get("filing_type"),
                        "source_file": result.get("source_file"),
                        "file_hash": result.get("file_hash"),
                    }
                )
            )

        return documents