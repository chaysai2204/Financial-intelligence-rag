import json
from pathlib import Path

OUTPUT_FILE = Path("evaluation/retrieval_questions.jsonl")

questions = [
    {
        "question_id": "Q046",
        "question": "What was Microsoft's revenue in fiscal 2025?",
        "category": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
        "retrieval_scope": "company_year",
        "expected_document_ids": [],
        "expected_tickers": ["MSFT"],
        "expected_years": [2025],
        "reference_answer": None,
        "evidence": [],
        "notes": "No Microsoft fiscal 2025 filing is available in the benchmark corpus. The system should abstain."
    },
    {
        "question_id": "Q047",
        "question": "What was NVIDIA's revenue in fiscal 2024?",
        "category": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
        "retrieval_scope": "company_year",
        "expected_document_ids": [],
        "expected_tickers": ["NVDA"],
        "expected_years": [2024],
        "reference_answer": None,
        "evidence": [],
        "notes": "NVIDIA fiscal 2024 is not available in the live benchmark corpus. The system should not substitute fiscal 2023."
    },
    {
        "question_id": "Q048",
        "question": "What was Apple's revenue in fiscal 2026?",
        "category": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
        "retrieval_scope": "company_year",
        "expected_document_ids": [],
        "expected_tickers": ["AAPL"],
        "expected_years": [2026],
        "reference_answer": None,
        "evidence": [],
        "notes": "No Apple fiscal 2026 filing is available in the benchmark corpus. The system should abstain."
    },
    {
        "question_id": "Q049",
        "question": "What was NVIDIA's net income in fiscal 2025?",
        "category": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
        "retrieval_scope": "company_year",
        "expected_document_ids": [],
        "expected_tickers": ["NVDA"],
        "expected_years": [2025],
        "reference_answer": None,
        "evidence": [],
        "notes": "No NVIDIA fiscal 2025 filing is available in the benchmark corpus. The system should abstain."
    },
    {
        "question_id": "Q050",
        "question": "How did Microsoft's revenue change from fiscal 2024 to fiscal 2025?",
        "category": "unanswerable",
        "difficulty": "medium",
        "answerable": False,
        "retrieval_scope": "temporal",
        "expected_document_ids": [],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024, 2025],
        "reference_answer": None,
        "evidence": [],
        "notes": "Fiscal 2025 evidence is unavailable in the benchmark corpus, so the requested temporal comparison cannot be supported."
    }
]

existing_ids = set()

if OUTPUT_FILE.exists():
    with OUTPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                existing_ids.add(json.loads(line)["question_id"])

to_add = [q for q in questions if q["question_id"] not in existing_ids]

if not to_add:
    print("Unanswerable questions already exist. Nothing added.")
else:
    needs_newline = (
        OUTPUT_FILE.exists()
        and OUTPUT_FILE.stat().st_size > 0
        and not OUTPUT_FILE.read_bytes().endswith(b"\n")
    )

    with OUTPUT_FILE.open("a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")

        for question in to_add:
            f.write(json.dumps(question) + "\n")

    print(f"Added {len(to_add)} unanswerable questions.")
    