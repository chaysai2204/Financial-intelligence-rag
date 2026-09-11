import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

from ingestion.file_validator import validate_pdf_file
from ingestion.pdf_to_markdown import PDFToMarkdownConverter
from ingestion.semantic_chunker import chunk_markdown
from ingestion.manifest_loader import load_manifest
from ingestion.parser_output_validator import validate_markdown_output
from ingestion.file_utils import compute_file_hash
from ingestion.document_validator import (
    DocumentValidationStatus,
    classify_financial_document,
)
from ingestion.metadata_extractor import extract_document_metadata

from vectorstore.azure_ai_search import AzureAISearchVectorStore
from vectorstore.azure_ai_search import Retriever

from rag.kpi_extractor_rag import extract_financial_metrics
from database.save_metrics import save_metrics


load_dotenv()


def ingest_document(
    pdf_path: str,
    embeddings,
    vector_store,
    extract_kpis: bool = True
) -> None:

    pdf_file = Path(pdf_path)

    # Step 0: Basic file validation
    validate_pdf_file(pdf_file)

    # Step 1: Compute stable file identity
    file_hash = compute_file_hash(pdf_file)

    # Step 2: Resolve metadata
    manifest = load_manifest()

    metadata = manifest.get(pdf_file.name)

    if metadata:
        print(
            f"Ingesting curated document {pdf_file.name} "
            f"as company={metadata.company!r}, "
            f"ticker={metadata.ticker!r}, "
            f"year={metadata.fiscal_year!r}, "
            f"filing_type={metadata.filing_type!r}"
        )

    else:
        # Unknown user upload
        validation_status, detected_type = (
            classify_financial_document(pdf_file)
        )

        if (
            validation_status
            == DocumentValidationStatus.INVALID_PDF
        ):
            raise ValueError(
                f"Invalid PDF: {pdf_file.name}"
            )

        if (
            validation_status
            == DocumentValidationStatus.UNREADABLE
        ):
            raise ValueError(
                f"Unable to reliably extract readable text "
                f"from {pdf_file.name}."
            )

        if (
            validation_status
            == DocumentValidationStatus.UNSUPPORTED
        ):
            raise ValueError(
                f"Unsupported document: {pdf_file.name}. "
                "Currently supported documents are "
                "10-Ks and annual reports."
            )

        print(
            f"Document validation passed: "
            f"{pdf_file.name} detected as {detected_type!r}"
        )

        # Extract metadata from document content
        metadata = extract_document_metadata(
            pdf_file
        )

        print(
            f"Extracted metadata from content: "
            f"company={metadata.company!r}, "
            f"ticker={metadata.ticker!r}, "
            f"year={metadata.fiscal_year!r}, "
            f"filing_type={metadata.filing_type!r}"
        )

    # Both curated + user upload paths converge here
    company = metadata.company
    year = str(metadata.fiscal_year)

    # Step 3: PDF -> Markdown
    converter = PDFToMarkdownConverter()

    markdown_file = converter.convert_pdf(
        pdf_path=pdf_path,
        output_dir="data/markdown"
    )

    print(
        f"Markdown created for {pdf_file.name}"
    )

    validate_markdown_output(markdown_file)

    print(
        f"Markdown validation passed for {pdf_file.name}"
    )

    # Step 4: Markdown -> chunks
    chunks = chunk_markdown(
        markdown_file=markdown_file,
        embeddings=embeddings
    )

    print(
        f"Generated {len(chunks)} chunks "
        f"for {pdf_file.name}"
    )

    # Step 5: Embed + upload to Azure AI Search
    vector_store.upload_chunks(
        chunks=chunks,
        embeddings=embeddings,
        document_id=metadata.document_id,
        company=metadata.company,
        ticker=metadata.ticker,
        year=str(metadata.fiscal_year),
        filing_type=metadata.filing_type,
        source_file=metadata.source_file,
        file_hash=file_hash
    )

    # Step 6: KPI extraction
    # Optional so corpus indexing can run without
    # unnecessary LLM calls and PostgreSQL inserts.
    if extract_kpis:

        metrics = extract_financial_metrics(
            retriever=Retriever(
                vector_store.client
            ),
            company=company,
            year=(
                int(year)
                if year.isdigit()
                else None
            )
        )

        if metrics:
            save_metrics(
                company=company,
                year=(
                    int(year)
                    if year.isdigit()
                    else None
                ),
                metrics=metrics
            )
    else:
        print(
            f"Skipping KPI extraction for "
            f"{pdf_file.name}"
        )


def ingest_directory(
    input_dir: str,
    extract_kpis: bool = False
) -> None:

    embeddings = AzureOpenAIEmbeddings(
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

    vector_store = AzureAISearchVectorStore(
        endpoint=os.getenv(
            "AZURE_SEARCH_ENDPOINT"
        ),
        api_key=os.getenv(
            "AZURE_SEARCH_API_KEY"
        ),
        index_name=os.getenv(
            "AZURE_SEARCH_INDEX_NAME"
        ),
    )

    pdf_files = list(
        Path(input_dir).rglob("*.pdf")
    )

    print(
        f"Found {len(pdf_files)} PDF(s)"
    )

    for pdf_file in pdf_files:

        print(
            f"\nProcessing {pdf_file}"
        )

        ingest_document(
            pdf_path=str(pdf_file),
            embeddings=embeddings,
            vector_store=vector_store,
            extract_kpis=extract_kpis
        )


if __name__ == "__main__":
    ingest_directory(
        "data/raw_pdfs",
        extract_kpis=False
    )