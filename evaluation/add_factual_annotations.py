import json
from pathlib import Path

DATASET_PATH = Path("evaluation/retrieval_questions.jsonl")

QUESTIONS = [
    {
        "question_id": "Q006",
        "question": "What were Apple's Services net sales in fiscal 2024?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2024],
        "reference_answer": "Apple's Services net sales in fiscal 2024 were $96.169 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Products and Services Performance",
                "evidence_text": "In millions. Services net sales were $96,169 million in 2024, compared with $85,200 million in 2023 and $78,129 million in 2022."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q007",
        "question": "What were Apple's total net sales in fiscal 2023?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2023_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023],
        "reference_answer": "Apple's total net sales in fiscal 2023 were $383.285 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Products and Services Performance",
                "evidence_text": "In millions. Total net sales were $383,285 million in 2023, compared with $394,328 million in 2022 and $365,817 million in 2021."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q008",
        "question": "What was Microsoft's total revenue in fiscal 2024?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": "Microsoft's total revenue in fiscal 2024 was $245.122 billion.",
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Consolidated Statements of Income",
                "evidence_text": "In millions. Total revenue was $245,122 million in 2024, $211,915 million in 2023, and $198,270 million in 2022."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q009",
        "question": "What was Microsoft's total revenue in fiscal 2023?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2023_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2023],
        "reference_answer": "Microsoft's total revenue in fiscal 2023 was $211.915 billion.",
        "evidence": [
            {
                "document_id": "MSFT_2023_10K",
                "section_hint": "Consolidated Statements of Income",
                "evidence_text": "In millions. Total revenue was $211,915 million in 2023, $198,270 million in 2022, and $168,088 million in 2021."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q010",
        "question": "What was NVIDIA's total revenue in fiscal 2023?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": "NVIDIA's total revenue in fiscal 2023 was $26.974 billion.",
        "evidence": [
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Fiscal Year 2023 Summary",
                "evidence_text": "In millions. Revenue was $26,974 million for the year ended January 29, 2023, compared with $26,914 million for the prior year."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q011",
        "question": "What was Apple's net income in fiscal 2024?",
        "category": "factual",
        "difficulty": "easy",
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
                "evidence_text": "In millions. Net income was $93,736 million in 2024, $96,995 million in 2023, and $99,803 million in 2022."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q012",
        "question": "What was Microsoft's net income in fiscal 2024?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": "Microsoft's net income in fiscal 2024 was $88.136 billion.",
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Fiscal Year 2024 Compared with Fiscal Year 2023",
                "evidence_text": "In millions. Net income was $88,136 million in 2024 compared with $72,361 million in 2023, an increase of 22%."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q013",
        "question": "How much revenue did NVIDIA generate from its Data Center business in fiscal 2023?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": "NVIDIA generated $15.005 billion in Data Center revenue in fiscal 2023.",
        "evidence": [
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Revenue by Specialized Markets",
                "evidence_text": "In millions. Data Center revenue was $15,005 million for the year ended January 29, 2023, compared with $10,613 million in fiscal 2022."
            }
        ],
        "notes": None
    },
    {
        "question_id": "Q014",
        "question": "What were Apple's iPhone net sales in fiscal 2023?",
        "category": "factual",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2023_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023],
        "reference_answer": "Apple's iPhone net sales in fiscal 2023 were $200.583 billion.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Products and Services Performance",
                "evidence_text": "In millions. iPhone net sales were $200,583 million in 2023, compared with $205,489 million in 2022 and $191,973 million in 2021."
            }
        ],
        "notes": None
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

    print(f"Added {added} factual questions.")


if __name__ == "__main__":
    main()