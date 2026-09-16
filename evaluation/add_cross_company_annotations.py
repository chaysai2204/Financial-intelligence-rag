import json
from pathlib import Path

OUTPUT_FILE = Path("evaluation/retrieval_questions.jsonl")

questions = [
    {
        "question_id": "Q033",
        "question": "How did Apple's fiscal 2024 revenue compare with Microsoft's fiscal 2024 revenue?",
        "category": "cross_company",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2024_10K", "MSFT_2024_10K"],
        "expected_tickers": ["AAPL", "MSFT"],
        "expected_years": [2024],
        "reference_answer": "Apple reported $391.035 billion in total net sales in fiscal 2024, compared with Microsoft's $245.122 billion in revenue. Apple's revenue was $145.913 billion higher.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Net Sales Disaggregated by Products and Services",
                "evidence_text": "In millions. Total net sales were $391,035 million in fiscal 2024."
            },
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Summary Results of Operations",
                "evidence_text": "In millions. Revenue was $245,122 million in fiscal 2024."
            }
        ],
        "notes": "Cross-company comparison requiring evidence from two filings."
    },
    {
        "question_id": "Q034",
        "question": "How did Apple's fiscal 2024 net income compare with Microsoft's fiscal 2024 net income?",
        "category": "cross_company",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2024_10K", "MSFT_2024_10K"],
        "expected_tickers": ["AAPL", "MSFT"],
        "expected_years": [2024],
        "reference_answer": "Apple reported fiscal 2024 net income of $93.736 billion, compared with Microsoft's $88.136 billion. Apple's net income was $5.600 billion higher.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Consolidated Statements of Operations",
                "evidence_text": "In millions. Net income was $93,736 million in fiscal 2024."
            },
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Summary Results of Operations",
                "evidence_text": "In millions. Net income was $88,136 million in fiscal 2024."
            }
        ],
        "notes": "Cross-company comparison requiring evidence from two filings."
    },
    {
        "question_id": "Q035",
        "question": "Which supply-chain risks were discussed by both Apple and NVIDIA?",
        "category": "cross_company",
        "difficulty": "hard",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2023_10K", "NVDA_2023_10K"],
        "expected_tickers": ["AAPL", "NVDA"],
        "expected_years": [2023],
        "reference_answer": "Both Apple and NVIDIA identified risks from dependence on external suppliers and manufacturers, supply or capacity constraints, and disruptions such as geopolitical events, natural disasters and other events that can interrupt manufacturing or product supply.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Business Risks - Supply and Manufacturing",
                "evidence_text": "Apple relies on single or limited sources for many critical components and outsourcing partners for manufacturing. Supplier or manufacturing disruptions, shortages, geopolitical events and other business interruptions can constrain supply and product delivery."
            },
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Risks Related to Demand, Supply and Manufacturing",
                "evidence_text": "NVIDIA depends on third-party suppliers, foundries and subcontractors, and identified risks including supply and capacity constraints, demand-estimation errors, natural disasters, pandemics and geopolitical tensions."
            }
        ],
        "notes": "Requires synthesizing overlapping supply-chain risks across two companies."
    },
    {
        "question_id": "Q036",
        "question": "How did Apple and Microsoft describe competitive pressures in their fiscal 2024 filings?",
        "category": "cross_company",
        "difficulty": "hard",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2024_10K", "MSFT_2024_10K"],
        "expected_tickers": ["AAPL", "MSFT"],
        "expected_years": [2024],
        "reference_answer": "Apple emphasized aggressive price competition, margin pressure, rapid technological change, short product cycles and the need for continual innovation. Microsoft described competition across numerous markets including productivity software, cloud and AI, operating systems, security and platform ecosystems from established technology companies, emerging competitors and open-source offerings.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Competition",
                "evidence_text": "Apple described highly competitive markets characterized by aggressive price competition, downward pressure on gross margins, frequent product introductions, short product life cycles, evolving standards and rapid technological advancement."
            },
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Competition",
                "evidence_text": "Microsoft described competition across its cloud, AI, productivity, operating system, security and other platform businesses from established technology companies, emerging competitors and open-source offerings."
            }
        ],
        "notes": "Requires qualitative synthesis of competitive pressures across two filings."
    },
    {
        "question_id": "Q037",
        "question": "How did Apple's fiscal 2023 revenue compare with Microsoft's fiscal 2023 revenue?",
        "category": "cross_company",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2023_10K", "MSFT_2023_10K"],
        "expected_tickers": ["AAPL", "MSFT"],
        "expected_years": [2023],
        "reference_answer": "Apple reported $383.285 billion in total net sales in fiscal 2023, compared with Microsoft's $211.915 billion in revenue. Apple's revenue was $171.370 billion higher.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Consolidated Statements of Operations",
                "evidence_text": "In millions. Total net sales were $383,285 million in fiscal 2023."
            },
            {
                "document_id": "MSFT_2023_10K",
                "section_hint": "Summary Results of Operations",
                "evidence_text": "In millions. Revenue was $211,915 million in fiscal 2023."
            }
        ],
        "notes": "Cross-company comparison requiring evidence from two filings."
    },
    {
        "question_id": "Q038",
        "question": "How did Apple and NVIDIA describe risks arising from third-party manufacturing relationships?",
        "category": "cross_company",
        "difficulty": "hard",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2023_10K", "NVDA_2023_10K"],
        "expected_tickers": ["AAPL", "NVDA"],
        "expected_years": [2023],
        "reference_answer": "Apple said outsourcing manufacturing reduces its direct control over production and distribution and exposes it to partner failures and disruptions. NVIDIA similarly said dependence on third-party foundries, suppliers and subcontractors reduces its control over product quantity, quality, manufacturing yields and delivery schedules.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Business Risks - Outsourcing Partners",
                "evidence_text": "Apple performs substantially all manufacturing through outsourcing partners, which reduces its direct control over production and distribution. Failures or disruptions at these partners can affect product quality, quantity, cost and supply."
            },
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Risks Related to Demand, Supply and Manufacturing",
                "evidence_text": "NVIDIA depends on third-party suppliers and foundries to manufacture, assemble, test and package products, reducing its control over product quantity and quality, manufacturing yields and product delivery schedules."
            }
        ],
        "notes": "Cross-company comparison focused specifically on third-party manufacturing dependence."
    },
    {
        "question_id": "Q039",
        "question": "How did Apple's fiscal 2023 net income compare with Microsoft's fiscal 2023 net income?",
        "category": "cross_company",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "cross_company",
        "expected_document_ids": ["AAPL_2023_10K", "MSFT_2023_10K"],
        "expected_tickers": ["AAPL", "MSFT"],
        "expected_years": [2023],
        "reference_answer": "Apple reported fiscal 2023 net income of $96.995 billion, compared with Microsoft's $72.361 billion. Apple's net income was $24.634 billion higher.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Consolidated Statements of Operations",
                "evidence_text": "In millions. Net income was $96,995 million in fiscal 2023."
            },
            {
                "document_id": "MSFT_2023_10K",
                "section_hint": "Summary Results of Operations",
                "evidence_text": "In millions. Net income was $72,361 million in fiscal 2023."
            }
        ],
        "notes": "Cross-company comparison requiring evidence from two filings."
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
    print("Cross-company questions already exist. Nothing added.")
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

    print(f"Added {len(to_add)} cross-company questions.")