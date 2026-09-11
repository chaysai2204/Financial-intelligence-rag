from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_markdown(markdown_file: str) -> str:
    """
    Read markdown content.
    """

    return Path(markdown_file).read_text(
        encoding="utf-8"
    )


def chunk_markdown(
    markdown_file: str,
    embeddings=None
) -> list[Document]:
    """
    Split markdown into deterministic chunks.

    The embeddings argument is kept temporarily
    so existing ingestion code does not need
    to change yet.
    """

    markdown_content = read_markdown(
        markdown_file
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=[
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    return splitter.create_documents(
        [markdown_content]
    )