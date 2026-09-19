import hashlib
import os
import time
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

from ingestion.file_utils import compute_file_hash
from ingestion.manifest_loader import load_manifest
from ingestion.structural_chunker import chunk_markdown_structural


load_dotenv(dotenv_path=".env")


EXPERIMENT_INDEX = "financial-documents-structural-v2"

BENCHMARK_PDFS = [
    #Path("data/raw_pdfs/apple/AAPL_2023_10-K.pdf"),
    Path("data/raw_pdfs/apple/AAPL_2024_10-K.pdf"),
    # Path("data/raw_pdfs/microsoft/MSFT_2023_10-K.pdf"),
    #Path("data/raw_pdfs/microsoft/MSFT_2024_10-K.pdf"),
    #Path("data/raw_pdfs/nvidia/NVDA_2023_10-K.pdf"),
]

MARKDOWN_DIR = Path("data/markdown")

# Keep requests modest because Azure OpenAI
# previously returned rate-limit errors.
EMBEDDING_BATCH_SIZE = 50

# Small pause between embedding batches.
BATCH_DELAY_SECONDS = 2


def build_embeddings():
    return AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv(
            "AZURE_OPENAI_ENDPOINT"
        ),
        api_key=os.getenv(
            "AZURE_OPENAI_API_KEY"
        ),
        azure_deployment=os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        ),
        api_version=os.getenv(
            "AZURE_OPENAI_API_VERSION"
        ),
    )


def build_search_client():
    baseline_index = os.getenv(
        "AZURE_SEARCH_INDEX_NAME"
    )

    if EXPERIMENT_INDEX == baseline_index:
        raise RuntimeError(
            "Experiment index matches baseline index. "
            "Aborting to protect baseline."
        )

    return SearchClient(
        endpoint=os.getenv(
            "AZURE_SEARCH_ENDPOINT"
        ),
        index_name=EXPERIMENT_INDEX,
        credential=AzureKeyCredential(
            os.getenv(
                "AZURE_SEARCH_API_KEY"
            )
        ),
    )


def embed_in_batches(
    texts: list[str],
    embeddings,
) -> list[list[float]]:
    vectors = []

    total_batches = (
        len(texts) + EMBEDDING_BATCH_SIZE - 1
    ) // EMBEDDING_BATCH_SIZE

    for start in range(
        0,
        len(texts),
        EMBEDDING_BATCH_SIZE,
    ):
        batch_number = (
            start // EMBEDDING_BATCH_SIZE
        ) + 1

        batch = texts[
            start:
            start + EMBEDDING_BATCH_SIZE
        ]

        print(
            f"  Embedding batch "
            f"{batch_number}/{total_batches} "
            f"({len(batch)} chunks)"
        )

        batch_vectors = embeddings.embed_documents(
            batch
        )

        vectors.extend(batch_vectors)

        if batch_number < total_batches:
            time.sleep(
                BATCH_DELAY_SECONDS
            )

    return vectors


def upload_document(
    pdf_path: Path,
    embeddings,
    search_client,
    manifest,
) -> int:

    print("\n" + "=" * 70)
    print(f"Processing: {pdf_path}")
    print("=" * 70)

    metadata = manifest.get(
        pdf_path.name
    )

    if metadata is None:
        raise ValueError(
            f"No manifest entry found for "
            f"{pdf_path.name}"
        )

    markdown_path = (
        MARKDOWN_DIR
        / f"{pdf_path.stem}.md"
    )

    if not markdown_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: "
            f"{markdown_path}"
        )

    file_hash = compute_file_hash(
        pdf_path
    )

    chunks = chunk_markdown_structural(
        str(markdown_path)
    )

    print(
        f"Generated {len(chunks)} "
        f"Structural v2 chunks"
    )

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    vectors = embed_in_batches(
        texts=texts,
        embeddings=embeddings,
    )

    if len(vectors) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    documents = []

    for chunk_index, (
        chunk,
        vector,
    ) in enumerate(
        zip(chunks, vectors)
    ):
        chunk_id = hashlib.sha256(
            (
                f"{file_hash}:"
                f"{chunk_index}"
            ).encode("utf-8")
        ).hexdigest()

        documents.append(
            {
                "id": chunk_id,
                "document_id":
                    metadata.document_id,
                "company":
                    metadata.company,
                "ticker":
                    metadata.ticker,
                "year":
                    str(metadata.fiscal_year),
                "filing_type":
                    metadata.filing_type,
                "source_file":
                    metadata.source_file,
                "file_hash":
                    file_hash,
                "chunk_index":
                    chunk_index,
                "content":
                    chunk.page_content,
                "content_vector":
                    vector,
            }
        )

    print(
        f"  Uploading "
        f"{len(documents)} chunks..."
    )

    result = search_client.upload_documents(
        documents
    )

    succeeded = sum(
        item.succeeded
        for item in result
    )

    failed = (
        len(result) - succeeded
    )

    print(
        f"  Uploaded: "
        f"{succeeded}/{len(documents)}"
    )

    if failed:
        print(
            f"  WARNING: "
            f"{failed} upload(s) failed"
        )

        for item in result:
            if not item.succeeded:
                print(
                    "   ",
                    item.key,
                    item.error_message,
                )

    return succeeded


def main():
    baseline_index = os.getenv(
        "AZURE_SEARCH_INDEX_NAME"
    )

    print(
        "Baseline index:",
        baseline_index,
    )
    print(
        "Experiment index:",
        EXPERIMENT_INDEX,
    )

    if baseline_index == EXPERIMENT_INDEX:
        raise RuntimeError(
            "Safety check failed."
        )

    print(
        "\nSafety check passed."
    )

    manifest = load_manifest()

    embeddings = build_embeddings()

    search_client = (
        build_search_client()
    )

    total_uploaded = 0

    for pdf_path in BENCHMARK_PDFS:

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: "
                f"{pdf_path}"
            )

        total_uploaded += upload_document(
            pdf_path=pdf_path,
            embeddings=embeddings,
            search_client=search_client,
            manifest=manifest,
        )

    print("\n" + "=" * 70)
    print("STRUCTURAL INGESTION COMPLETE")
    print("=" * 70)
    print(
        f"Total chunks uploaded: "
        f"{total_uploaded}"
    )
    print(
        f"Index: {EXPERIMENT_INDEX}"
    )


if __name__ == "__main__":
    main()