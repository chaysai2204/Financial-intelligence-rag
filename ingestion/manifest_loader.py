import csv
from pathlib import Path

from ingestion.document_metadata import DocumentMetadata


def load_manifest(manifest_path: str = "data/dataset_manifest.csv") -> dict[str, DocumentMetadata]:
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_file}")

    documents = {}

    with manifest_file.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            metadata = DocumentMetadata(
                document_id=row["document_id"],
                company=row["company"],
                ticker=row["ticker"],
                fiscal_year=int(row["fiscal_year"]),
                filing_type=row["filing_type"],
                source_file=row["source_file"],
                source_url=row.get("source_url", ""),
            )

            documents[metadata.source_file] = metadata

    return documents