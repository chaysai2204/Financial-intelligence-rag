import re
from enum import Enum
from pathlib import Path

import pymupdf


class DocumentValidationStatus(Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNREADABLE = "unreadable"
    INVALID_PDF = "invalid_pdf"


SUPPORTED_SIGNALS = {
    "10-K": [
        "form 10-k",
        "annual report pursuant to section 13",
        "securities exchange act of 1934",
    ],
    "annual_report": [
        "annual report",
        "fiscal year ended",
    ],
}


COMMON_WORDS = {
    "the",
    "of",
    "and",
    "to",
    "in",
    "for",
    "a",
    "is",
    "on",
    "that",
    "as",
    "by",
    "with",
    "from",
    "our",
    "we",
}


def extract_initial_text(
    pdf_path: str | Path,
    max_pages: int = 10
) -> str:
    """
    Extract text from the first few pages of a PDF.
    """

    pdf_path = Path(pdf_path)

    try:
        document = pymupdf.open(pdf_path)
    except Exception as exc:
        raise ValueError(f"Unable to open PDF: {exc}") from exc

    text_parts = []

    pages_to_read = min(max_pages, len(document))

    for page_number in range(pages_to_read):
        page = document[page_number]
        text_parts.append(page.get_text())

    document.close()

    return "\n".join(text_parts)


def normalize_text(text: str) -> str:
    """
    Normalize whitespace and capitalization.
    """

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_text_extraction_usable(text: str) -> bool:
    """
    Check whether extracted text looks like readable English prose.

    This checks extraction quality only.
    It does not classify whether the document is financial.
    """

    if not text or len(text.strip()) < 100:
        return False

    words = re.findall(r"[a-z]+", text.lower())

    if len(words) < 20:
        return False

    common_word_count = sum(
        word in COMMON_WORDS
        for word in words
    )

    common_word_ratio = (
        common_word_count / len(words)
    )

    if common_word_ratio < 0.03:
        return False

    return True


def classify_financial_document(
    pdf_path: str | Path
) -> tuple[DocumentValidationStatus, str | None]:
    """
    Validate and classify an uploaded PDF.
    """

    try:
        raw_text = extract_initial_text(pdf_path)
    except ValueError:
        return DocumentValidationStatus.INVALID_PDF, None

    if not is_text_extraction_usable(raw_text):
        return DocumentValidationStatus.UNREADABLE, None

    text = normalize_text(raw_text)

    ten_k_signals = SUPPORTED_SIGNALS["10-K"]

    ten_k_matches = sum(
        signal in text
        for signal in ten_k_signals
    )

    if ten_k_matches >= 1:
        return DocumentValidationStatus.SUPPORTED, "10-K"

    annual_report_signals = SUPPORTED_SIGNALS[
        "annual_report"
    ]

    annual_report_matches = sum(
        signal in text
        for signal in annual_report_signals
    )

    if annual_report_matches >= 2:
        return DocumentValidationStatus.SUPPORTED, "annual_report"

    return DocumentValidationStatus.UNSUPPORTED, None