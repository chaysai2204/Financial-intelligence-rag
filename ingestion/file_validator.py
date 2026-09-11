from pathlib import Path

import pymupdf


def validate_pdf_file(file_path: str | Path) -> None:
    """
    Basic validation before expensive ingestion work.

    Checks:
    - file exists
    - file is not empty
    - extension is .pdf
    - file can actually be opened as a PDF
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError(
            f"File does not exist: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    if file_path.stat().st_size == 0:
        raise ValueError(
            f"File is empty: {file_path.name}"
        )

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Unsupported file type: {file_path.name}. "
            "Only PDF files are supported."
        )

    try:
        document = pymupdf.open(file_path)
    except Exception as exc:
        raise ValueError(
            f"File is not a valid PDF: {file_path.name}"
        ) from exc

    if len(document) == 0:
        document.close()

        raise ValueError(
            f"PDF contains no pages: {file_path.name}"
        )

    document.close()