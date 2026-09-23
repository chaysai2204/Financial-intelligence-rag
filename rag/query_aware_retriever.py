import re
from dataclasses import dataclass


COMPANY_ALIASES = {
    "Apple": [
        r"\bapple\b",
        r"\baapl\b",
    ],
    "Microsoft": [
        r"\bmicrosoft\b",
        r"\bmsft\b",
    ],
    "NVIDIA": [
        r"\bnvidia\b",
        r"\bnvda\b",
    ],
    "Amazon": [
        r"\bamazon\b",
        r"\bamzn\b",
    ],
    "Alphabet": [
        r"\balphabet\b",
        r"\bgoogle\b",
        r"\bgoogl\b",
    ],
}


@dataclass(frozen=True)
class RetrievalTarget:
    company: str | None = None
    year: int | None = None


def detect_companies(question: str) -> list[str]:
    question_lower = question.lower()

    companies = []

    for company, patterns in COMPANY_ALIASES.items():
        for pattern in patterns:
            if re.search(pattern, question_lower):
                companies.append(company)
                break

    return companies


def detect_years(question: str) -> list[int]:
    years = re.findall(
        r"\b(20\d{2})\b",
        question,
    )

    return sorted(
        {
            int(year)
            for year in years
        }
    )


def build_retrieval_targets(
    question: str,
) -> list[RetrievalTarget]:

    companies = detect_companies(question)
    years = detect_years(question)

    # Example:
    # Apple + Microsoft + 2024
    #
    # → Apple/2024
    # → Microsoft/2024

    if companies and len(years) == 1:
        return [
            RetrievalTarget(
                company=company,
                year=years[0],
            )
            for company in companies
        ]

    # Example:
    # Apple 2023 vs 2024
    #
    # → Apple/2023
    # → Apple/2024

    if len(companies) == 1 and len(years) > 1:
        return [
            RetrievalTarget(
                company=companies[0],
                year=year,
            )
            for year in years
        ]

    # Simple company-specific question.
    #
    # "What risks did NVIDIA discuss?"
    #
    # → NVIDIA only

    if len(companies) == 1:
        return [
            RetrievalTarget(
                company=companies[0],
            )
        ]

    # Multiple companies without explicit year.
    if len(companies) > 1:
        return [
            RetrievalTarget(
                company=company,
            )
            for company in companies
        ]

    # No deterministic metadata detected.
    return []


def _document_key(doc):
    metadata = doc.metadata

    return (
        metadata.get("document_id"),
        metadata.get("chunk_index"),
    )


def query_aware_retrieve(
    *,
    retriever,
    question: str,
    final_top_k: int = 5,
    per_target_k: int = 5,
):
    """
    Retrieve evidence using deterministic company/year
    targets when the question contains them.

    If no target can be identified, fall back to the
    normal global Dense retrieval.
    """

    targets = build_retrieval_targets(
        question
    )

    if not targets:
        return retriever.invoke(
            query=question,
            top_k=final_top_k,
        )

    grouped_docs = []

    for target in targets:

        kwargs = {
            "query": question,
            "top_k": per_target_k,
        }

        if target.company:
            kwargs["company"] = (
                target.company
            )

        if target.year:
            kwargs["year"] = (
                target.year
            )

        docs = retriever.invoke(
            **kwargs
        )

        grouped_docs.append(docs)

    # ---------------------------------
    # Balanced round-robin merge
    # ---------------------------------
    #
    # Important for questions like:
    #
    # Apple vs Microsoft
    #
    # We do NOT want all top-5 chunks
    # to come from one company.
    # ---------------------------------

    merged = []
    seen = set()

    position = 0

    while len(merged) < final_top_k:

        added_any = False

        for docs in grouped_docs:

            if position >= len(docs):
                continue

            doc = docs[position]

            key = _document_key(doc)

            if key not in seen:
                seen.add(key)
                merged.append(doc)

                added_any = True

                if len(merged) >= final_top_k:
                    break

        if not added_any:
            break

        position += 1

    return merged