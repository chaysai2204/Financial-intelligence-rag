import json
from pathlib import Path

DATASET_PATH = Path("evaluation/retrieval_questions.jsonl")

QUESTIONS = [
    {
        "question_id": "Q027",
        "question": "How did Apple's Services net sales change from fiscal 2023 to fiscal 2024?",
        "category": "temporal",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023, 2024],
        "reference_answer": "Apple's Services net sales increased from $85.200 billion in fiscal 2023 to $96.169 billion in fiscal 2024, an increase of $10.969 billion, or approximately 12.9%.",
        "evidence": [{
            "document_id": "AAPL_2024_10K",
            "section_hint": "Products and Services Performance",
            "evidence_text": "Services net sales were $96,169 million in fiscal 2024 and $85,200 million in fiscal 2023."
        }],
        "notes": "Both years are available in the fiscal 2024 comparative table."
    },
    {
        "question_id": "Q028",
        "question": "How did Apple's net income change from fiscal 2023 to fiscal 2024?",
        "category": "temporal",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023, 2024],
        "reference_answer": "Apple's net income decreased from $96.995 billion in fiscal 2023 to $93.736 billion in fiscal 2024, a decrease of $3.259 billion, or approximately 3.4%.",
        "evidence": [{
            "document_id": "AAPL_2024_10K",
            "section_hint": "Consolidated Statements of Operations",
            "evidence_text": "Net income was $93,736 million in fiscal 2024 and $96,995 million in fiscal 2023."
        }],
        "notes": "Both years are available in the fiscal 2024 comparative financial statements."
    },
    {
        "question_id": "Q029",
        "question": "How did Microsoft's total revenue change from fiscal 2023 to fiscal 2024?",
        "category": "temporal",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2023, 2024],
        "reference_answer": "Microsoft's revenue increased from $211.915 billion in fiscal 2023 to $245.122 billion in fiscal 2024, an increase of $33.207 billion, or approximately 15.7%.",
        "evidence": [{
            "document_id": "MSFT_2024_10K",
            "section_hint": "Summary Results of Operations",
            "evidence_text": "Revenue was $245,122 million in fiscal 2024 and $211,915 million in fiscal 2023, representing a 16% increase."
        }],
        "notes": "The filing reports the year-over-year increase as 16% after rounding."
    },
    {
        "question_id": "Q030",
        "question": "How did Microsoft's net income change from fiscal 2023 to fiscal 2024?",
        "category": "temporal",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2023, 2024],
        "reference_answer": "Microsoft's net income increased from $72.361 billion in fiscal 2023 to $88.136 billion in fiscal 2024, an increase of $15.775 billion, or approximately 21.8%.",
        "evidence": [{
            "document_id": "MSFT_2024_10K",
            "section_hint": "Summary Results of Operations",
            "evidence_text": "Net income was $88,136 million in fiscal 2024 and $72,361 million in fiscal 2023, representing a 22% increase."
        }],
        "notes": "The filing reports the year-over-year increase as 22% after rounding."
    },
    {
        "question_id": "Q031",
        "question": "How did Apple's iPhone net sales change between fiscal 2023 and fiscal 2024?",
        "category": "temporal",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023, 2024],
        "reference_answer": "Apple's iPhone net sales increased slightly from $200.583 billion in fiscal 2023 to $201.183 billion in fiscal 2024, an increase of $600 million, or approximately 0.3%.",
        "evidence": [{
            "document_id": "AAPL_2024_10K",
            "section_hint": "Products and Services Performance",
            "evidence_text": "iPhone net sales were $201,183 million in fiscal 2024 and $200,583 million in fiscal 2023. Apple described iPhone net sales as relatively flat year over year."
        }],
        "notes": "Tests retrieval of a small year-over-year change."
    },
    {
        "question_id": "Q032",
        "question": "How did Apple's Services contribution to total net sales change from fiscal 2023 to fiscal 2024?",
        "category": "temporal",
        "difficulty": "hard",
        "answerable": True,
        "retrieval_scope": "temporal",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023, 2024],
        "reference_answer": "Services represented approximately 22.2% of Apple's total net sales in fiscal 2023 and approximately 24.6% in fiscal 2024, an increase of about 2.4 percentage points.",
        "evidence": [{
            "document_id": "AAPL_2024_10K",
            "section_hint": "Products and Services Performance",
            "evidence_text": "Services net sales were $96,169 million in 2024 and $85,200 million in 2023, while total net sales were $391,035 million in 2024 and $383,285 million in 2023."
        }],
        "notes": "Requires calculating Services net sales as a percentage of total net sales for both years."
    }
]


def main():
    existing_ids = set()

    if DATASET_PATH.exists():
        with DATASET_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_ids.add(json.loads(line)["question_id"])

    added = 0

    if DATASET_PATH.exists() and DATASET_PATH.stat().st_size > 0:
        if not DATASET_PATH.read_bytes().endswith(b"\n"):
            with DATASET_PATH.open("ab") as f:
                f.write(b"\n")

    with DATASET_PATH.open("a", encoding="utf-8") as f:
        for question in QUESTIONS:
            if question["question_id"] in existing_ids:
                print(f"Skipping {question['question_id']} - already exists.")
                continue

            f.write(json.dumps(question) + "\n")
            added += 1

    print(f"Added {added} temporal questions.")


if __name__ == "__main__":
    main()