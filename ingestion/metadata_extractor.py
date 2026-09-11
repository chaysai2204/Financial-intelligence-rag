import re
from pathlib import Path

from ingestion.document_metadata import DocumentMetadata
from ingestion.document_validator import extract_initial_text


COMPANY_ALIASES = {
    "apple inc.": ("Apple", "AAPL"),
    "microsoft corporation": ("Microsoft", "MSFT"),
    "alphabet inc.": ("Alphabet", "GOOGL"),
    "amazon.com, inc.": ("Amazon", "AMZN"),
    "nvidia corporation": ("NVIDIA", "NVDA"),
}


def extract_fiscal_year(text: str) -> int | None:
    """
    Extract fiscal year from the document header.

    Examples:
    For the fiscal year ended September 28, 2024
    For the fiscal year ended January 28, 2024
    """

    pattern = (
        r"fiscal\s+year\s+ended\s+"
        r"[A-Za-z]+\.?\s+\d{1,2},?\s+(\d{4})"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    # Small fallback for filings whose PDF extraction
    # does not preserve the full "year ended" phrase.
    fallback_pattern = r"\bfiscal\s+year\s+(\d{4})\b"

    match = re.search(
        fallback_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


def extract_filing_type(text: str) -> str | None:
    """
    Detect supported filing type.
    """

    if re.search(
        r"\bform\s+10-k\b",
        text,
        re.IGNORECASE
    ):
        return "10-K"

    if re.search(
        r"\bannual\s+report\b",
        text,
        re.IGNORECASE
    ):
        return "annual_report"

    return None


def extract_company_and_ticker(
    text: str
) -> tuple[str | None, str | None]:
    """
    Detect company from the document cover page.
    """

    normalized = re.sub(r"\s+", " ", text.lower()).strip()

    for company_text, (
        company,
        ticker
    ) in COMPANY_ALIASES.items():

        if company_text in normalized:
            return company, ticker

    return None, None


def extract_document_metadata(
    pdf_path: str | Path
) -> DocumentMetadata:
    """
    Extract normalized document metadata from PDF content.

    Company detection uses only the first page so that
    competitor names later in the filing do not cause
    incorrect company classification.
    """

    pdf_path = Path(pdf_path)

    # Company should come from the cover page.
    cover_text = extract_initial_text(
        pdf_path,
        max_pages=1
    )

    # Filing type/year should also appear near the beginning.
    header_text = extract_initial_text(
        pdf_path,
        max_pages=3
    )

    company, ticker = extract_company_and_ticker(
        cover_text
    )

    fiscal_year = extract_fiscal_year(
        header_text
    )

    filing_type = extract_filing_type(
        header_text
    )

    missing_fields = []

    if not company:
        missing_fields.append("company")

    if not ticker:
        missing_fields.append("ticker")

    if not fiscal_year:
        missing_fields.append("fiscal_year")

    if not filing_type:
        missing_fields.append("filing_type")

    if missing_fields:
        raise ValueError(
            "Unable to reliably extract metadata fields: "
            + ", ".join(missing_fields)
        )

    document_id = (
        f"{ticker}_{fiscal_year}_"
        f"{filing_type.replace('-', '')}"
    )

    return DocumentMetadata(
        document_id=document_id,
        company=company,
        ticker=ticker,
        fiscal_year=fiscal_year,
        filing_type=filing_type,
        source_file=pdf_path.name,
        source_url=""
    )