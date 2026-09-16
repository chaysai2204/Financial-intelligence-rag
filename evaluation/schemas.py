from typing import Literal
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    document_id: str
    section_hint: str | None = None
    evidence_text: str


class EvaluationQuestion(BaseModel):
    question_id: str
    question: str

    category: Literal[
        "factual",
        "paraphrase",
        "qualitative",
        "temporal",
        "cross_company",
        "evidence_seeking",
        "unanswerable",
    ]

    difficulty: Literal[
        "easy",
        "medium",
        "hard",
    ]

    answerable: bool

    retrieval_scope: Literal[
        "global",
        "company",
        "company_year",
        "temporal",
        "cross_company",
    ]

    expected_document_ids: list[str]
    expected_tickers: list[str]
    expected_years: list[int]

    reference_answer: str | None = None
    evidence: list[EvidenceItem]

    notes: str | None = None