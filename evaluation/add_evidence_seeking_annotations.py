import json
from pathlib import Path

OUTPUT_FILE = Path("evaluation/retrieval_questions.jsonl")

questions = [
    {
        "question_id": "Q040",
        "question": "What evidence does Apple provide about the importance of Services to its fiscal 2024 sales?",
        "category": "evidence_seeking",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2024],
        "reference_answer": (
            "Apple reported $96.169 billion in Services net sales in fiscal 2024, "
            "up from $85.200 billion in fiscal 2023. Apple also stated that higher "
            "Services net sales contributed to year-over-year sales growth in several "
            "geographic regions, including the Americas, Europe, and Rest of Asia Pacific."
        ),
        "evidence": [{
            "document_id": "AAPL_2024_10K",
            "section_hint": "Products and Services Performance / Geographic Performance",
            "evidence_text": (
                "Services net sales were $96,169 million in fiscal 2024 and $85,200 "
                "million in fiscal 2023. Apple also stated that higher Services net "
                "sales contributed to sales growth in the Americas, Europe, and Rest "
                "of Asia Pacific."
            )
        }],
        "notes": "Evidence-seeking question requiring retrieval of evidence demonstrating Services' contribution to sales."
    },
    {
        "question_id": "Q041",
        "question": "What evidence does Microsoft provide about the performance of its cloud business in fiscal 2024?",
        "category": "evidence_seeking",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": (
            "Microsoft reported that Server products and cloud services revenue "
            "increased 22% in fiscal 2024, driven by 30% growth in Azure and other "
            "cloud services."
        ),
        "evidence": [{
            "document_id": "MSFT_2024_10K",
            "section_hint": "Results of Operations",
            "evidence_text": (
                "Server products and cloud services revenue increased 22% driven "
                "by Azure and other cloud services growth of 30%."
            )
        }],
        "notes": "Uses explicit fiscal 2024 cloud growth evidence."
    },
    {
        "question_id": "Q042",
        "question": "What evidence does NVIDIA provide that it relies heavily on external manufacturing partners?",
        "category": "evidence_seeking",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": (
            "NVIDIA states that it depends on foundries to manufacture its semiconductor "
            "wafers and contracts with independent subcontractors rather than assembling, "
            "testing, or packaging its products itself. It says this third-party dependence "
            "reduces its control over quantity, quality, manufacturing yields and delivery schedules."
        ),
        "evidence": [{
            "document_id": "NVDA_2023_10K",
            "section_hint": "Risks Related to Demand, Supply and Manufacturing",
            "evidence_text": (
                "NVIDIA depends on foundries to manufacture its semiconductor wafers "
                "and contracts with independent subcontractors for assembly, testing "
                "and packaging. Dependency on third-party suppliers reduces its control "
                "over product quantity, quality, manufacturing yields and delivery schedules."
            )
        }],
        "notes": "Direct evidence of NVIDIA's fabless and outsourced manufacturing model."
    },
    {
        "question_id": "Q043",
        "question": "What evidence does Apple provide that international markets are important to its business?",
        "category": "evidence_seeking",
        "difficulty": "easy",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2023_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023],
        "reference_answer": (
            "Apple states that sales outside the United States represent a majority "
            "of its total net sales. It also operates a large global supply chain, "
            "with a majority of supplier facilities located outside the United States."
        ),
        "evidence": [{
            "document_id": "AAPL_2023_10K",
            "section_hint": "Macroeconomic and Industry Risks",
            "evidence_text": (
                "Apple has international operations with sales outside the U.S. "
                "representing a majority of total net sales, and a majority of its "
                "supplier facilities, including manufacturing and assembly sites, "
                "are located outside the U.S."
            )
        }],
        "notes": "Direct evidence of Apple's international sales and operational exposure."
    },
    {
        "question_id": "Q044",
        "question": "What evidence does NVIDIA provide that demand forecasting can affect its financial performance?",
        "category": "evidence_seeking",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": (
            "NVIDIA states that inaccurate customer-demand estimates can create "
            "significant mismatches between supply and demand. These mismatches have "
            "resulted in product shortages and excess inventory and have significantly "
            "harmed its financial results."
        ),
        "evidence": [{
            "document_id": "NVDA_2023_10K",
            "section_hint": "Risks Related to Demand, Supply and Manufacturing",
            "evidence_text": (
                "If NVIDIA's estimates of customer demand are inaccurate, there can "
                "be a significant mismatch between supply and demand. NVIDIA states "
                "that this has resulted in product shortages and excess inventory "
                "and has significantly harmed its financial results."
            )
        }],
        "notes": "Direct connection between demand-forecasting errors and financial performance."
    },
    {
        "question_id": "Q045",
        "question": "What evidence does Microsoft provide about the importance of cloud services to its business?",
        "category": "evidence_seeking",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": (
            "Microsoft describes Azure as the foundation of Microsoft Cloud and "
            "includes Azure and other cloud services within its Intelligent Cloud "
            "segment. In fiscal 2024, Server products and cloud services revenue "
            "increased 22%, driven by 30% growth in Azure and other cloud services."
        ),
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Intelligent Cloud",
                "evidence_text": (
                    "Microsoft describes Azure as the foundation of Microsoft Cloud "
                    "and includes Azure and other cloud services in its Intelligent Cloud segment."
                )
            },
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Results of Operations",
                "evidence_text": (
                    "Server products and cloud services revenue increased 22% driven "
                    "by Azure and other cloud services growth of 30%."
                )
            }
        ],
        "notes": "Combines strategic and financial evidence of cloud's importance."
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
    print("Evidence-seeking questions already exist. Nothing added.")
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

    print(f"Added {len(to_add)} evidence-seeking questions.")