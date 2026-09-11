import hashlib

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from types import SimpleNamespace


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
        year: int | None = None,
        top_k: int = 20
    ) -> list:

        filter_expr = None

        if company and year:

            filter_expr = (
                f"company eq '{company}' "
                f"and year eq '{year}'"
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

        for result in results:

            content = result.get(
                "content",
                ""
            )

            documents.append(
                SimpleNamespace(
                    page_content=content
                )
            )

        return documents