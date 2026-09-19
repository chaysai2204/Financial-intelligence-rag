from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker


def read_markdown(markdown_file: str) -> str:
    """
    Read markdown content.
    """

    return Path(markdown_file).read_text(
        encoding="utf-8"
    )


def chunk_markdown_semantic(
    markdown_file: str,
    embeddings,
) -> list[Document]:
    """
    Experimental semantic chunking strategy.

    Uses embedding-distance changes between neighboring
    sentence groups to determine chunk boundaries.

    This is kept separate from the recursive baseline
    so the baseline remains reproducible.
    """

    markdown_content = read_markdown(
        markdown_file
    )

    splitter = SemanticChunker(
        embeddings=embeddings,
        buffer_size=1,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=95,
        min_chunk_size=250,
    )

    return splitter.create_documents(
        [markdown_content]
    )