import json
from pathlib import Path

DATASET_PATH = Path("evaluation/retrieval_questions.jsonl")

QUESTIONS = [
    {
        "question_id": "Q015",
        "question": "How much profit did Apple keep after all expenses in fiscal 2024?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2024],
        "reference_answer": "Apple's net income in fiscal 2024 was $93.736 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Consolidated Statements of Operations",
                "evidence_text": "In millions. Net income was $93,736 million in fiscal 2024."
            }
        ],
        "notes": "Uses everyday wording for net income to test retrieval under terminology mismatch."
    },
    {
        "question_id": "Q016",
        "question": "How much money did Microsoft generate from customers in fiscal 2024?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": "Microsoft generated $245.122 billion in revenue in fiscal 2024.",
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Summary Results of Operations",
                "evidence_text": "In millions. Revenue was $245,122 million in fiscal 2024 compared with $211,915 million in fiscal 2023."
            }
        ],
        "notes": "Uses non-filing wording for revenue to test paraphrase retrieval."
    },
    {
        "question_id": "Q017",
        "question": "How much did NVIDIA earn from sales during fiscal 2023?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": "NVIDIA generated $26.974 billion in revenue in fiscal 2023.",
        "evidence": [
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Fiscal Year 2023 Summary",
                "evidence_text": "In millions. Revenue was $26,974 million for the year ended January 29, 2023."
            }
        ],
        "notes": "Uses 'earn from sales' instead of the filing term revenue."
    },
    {
        "question_id": "Q018",
        "question": "How much did Apple make from its services business during fiscal 2023?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2023_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023],
        "reference_answer": "Apple's Services net sales in fiscal 2023 were $85.200 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Products and Services Performance",
                "evidence_text": "In millions. Services net sales were $85,200 million in fiscal 2023."
            }
        ],
        "notes": "Uses conversational wording instead of Services net sales."
    },
    {
        "question_id": "Q019",
        "question": "How much profit remained for Microsoft shareholders in fiscal 2023?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2023_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2023],
        "reference_answer": "Microsoft's net income in fiscal 2023 was $72.361 billion.",
        "evidence": [
            {
                "document_id": "MSFT_2023_10K",
                "section_hint": "Fiscal Year 2023 Compared with Fiscal Year 2022",
                "evidence_text": "In millions. Net income was $72,361 million in fiscal 2023."
            }
        ],
        "notes": "Uses conversational wording for net income."
    },
    {
        "question_id": "Q020",
        "question": "How much money did Apple generate from iPhone sales during fiscal 2024?",
        "category": "paraphrase",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2024],
        "reference_answer": "Apple's iPhone net sales in fiscal 2024 were $201.183 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Products and Services Performance",
                "evidence_text": "In millions. iPhone net sales were $201,183 million in fiscal 2024."
            }
        ],
        "notes": "Uses conversational wording instead of iPhone net sales."
    }
]


def main():
    existing_ids = set()

    if DATASET_PATH.exists():
        with DATASET_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    existing_ids.add(json.loads(line)["question_id"])

    added = 0

    # Ensure existing JSONL ends with a newline before appending.
    if DATASET_PATH.exists() and DATASET_PATH.stat().st_size > 0:
        content = DATASET_PATH.read_bytes()

        if not content.endswith(b"\n"):
            with DATASET_PATH.open("ab") as file:
                file.write(b"\n")

    with DATASET_PATH.open("a", encoding="utf-8") as file:
        for question in QUESTIONS:
            if question["question_id"] in existing_ids:
                print(f"Skipping {question['question_id']} - already exists.")
                continue

            file.write(json.dumps(question) + "\n")
            added += 1

    print(f"Added {added} paraphrase questions.")


if __name__ == "__main__":
    main()