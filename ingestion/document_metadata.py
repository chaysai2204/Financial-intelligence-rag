from dataclasses import dataclass


@dataclass
class DocumentMetadata:
    document_id: str
    company: str
    ticker: str
    fiscal_year: int
    filing_type: str
    source_file: str
    source_url: str = ""