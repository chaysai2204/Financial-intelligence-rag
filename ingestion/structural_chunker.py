import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


MAX_CHUNK_SIZE = 1500
TARGET_MIN_SIZE = 750
CHUNK_OVERLAP = 200


def read_markdown(markdown_file: str) -> str:
    """
    Read markdown content.
    """

    return Path(markdown_file).read_text(
        encoding="utf-8"
    )


def split_into_sections(markdown_content: str) -> list[str]:
    """
    Split Markdown at H1/H2 headings while keeping
    each heading attached to its following content.
    """

    sections = re.split(
        r"(?=^#{1,2}\s)",
        markdown_content,
        flags=re.MULTILINE,
    )

    return [
        section.strip()
        for section in sections
        if section.strip()
    ]


def merge_small_sections(
    sections: list[str],
) -> list[str]:
    """
    Merge neighboring small Markdown sections while
    preserving their headings.

    Sections are accumulated until adding another
    section would exceed the maximum chunk size.
    """

    merged_sections = []
    current = ""

    for section in sections:
        candidate = (
            f"{current}\n\n{section}".strip()
            if current
            else section
        )

        if len(candidate) <= MAX_CHUNK_SIZE:
            current = candidate

            if len(current) >= TARGET_MIN_SIZE:
                merged_sections.append(current)
                current = ""

        else:
            if current:
                merged_sections.append(current)
                current = ""

            if len(section) <= MAX_CHUNK_SIZE:
                current = section
            else:
                merged_sections.append(section)

    if current:
        merged_sections.append(current)

    return merged_sections


def chunk_markdown_structural(
    markdown_file: str,
) -> list[Document]:
    """
    Structure-aware experimental chunker.

    Markdown headings define natural document sections.
    Small neighboring sections are merged while keeping
    their headings. Oversized sections are recursively
    split using paragraph and sentence boundaries.
    """

    markdown_content = read_markdown(
        markdown_file
    )

    sections = split_into_sections(
        markdown_content
    )

    merged_sections = merge_small_sections(
        sections
    )

    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = []

    for section in merged_sections:
        if len(section) <= MAX_CHUNK_SIZE:
            chunks.append(
                Document(
                    page_content=section
                )
            )
            continue

        section_chunks = fallback_splitter.create_documents(
            [section]
        )

        chunks.extend(section_chunks)

    return chunks