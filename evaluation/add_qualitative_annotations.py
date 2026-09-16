import json
from pathlib import Path

DATASET_PATH = Path("evaluation/retrieval_questions.jsonl")

questions = [
    {
        "question_id": "Q021",
        "question": "What risks did Apple identify related to its global supply chain in fiscal 2024?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2024_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2024],
        "reference_answer": "Apple identified supply-chain risks including reliance on outsourced manufacturing and logistics partners, supplier concentration, component shortages, trade restrictions, geopolitical tensions, natural disasters, and other disruptions that could affect production and distribution.",
        "evidence": [
            {
                "document_id": "AAPL_2024_10K",
                "section_hint": "Risk Factors - Supply Chain",
                "evidence_text": "Apple's global supply chain is subject to risks including outsourcing and supplier concentration, component availability, trade restrictions and geopolitical tensions, natural disasters, and other disruptions that could affect manufacturing and distribution."
            }
        ],
        "notes": "Qualitative synthesis of multiple supply-chain risks."
    },
    {
        "question_id": "Q022",
        "question": "What competitive pressures did Microsoft discuss in its fiscal 2024 filing?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": "Microsoft described competition across its cloud, AI, security, server, database, business intelligence, and other software businesses from large technology companies, specialized vendors, emerging AI companies, and open-source offerings.",
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Competition",
                "evidence_text": "Microsoft described competition across Azure, AI, security, server products, databases, business intelligence, and other offerings from companies including Amazon, Google, IBM, Oracle, specialized vendors, emerging AI competitors, and open-source offerings."
            }
        ],
        "notes": "Qualitative synthesis across Microsoft's competition discussion."
    },
    {
        "question_id": "Q023",
        "question": "What factors did NVIDIA identify as making demand forecasting difficult in fiscal 2023?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": "NVIDIA said demand forecasting is difficult because of factors including product transitions, estimates from customers and channel partners, new and emerging use cases, cryptocurrency-related demand, and rapidly changing or volatile market conditions.",
        "evidence": [
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Risk Factors - Demand Forecasting",
                "evidence_text": "NVIDIA described demand forecasting uncertainty arising from product transitions, customer and channel-partner estimates, new use cases, cryptocurrency-related demand, and changing or volatile market conditions."
            }
        ],
        "notes": "Requires synthesis of several demand-forecasting factors."
    },
    {
        "question_id": "Q024",
        "question": "What risks did Apple identify from depending on third-party suppliers and manufacturing partners in fiscal 2023?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["AAPL_2023_10K"],
        "expected_tickers": ["AAPL"],
        "expected_years": [2023],
        "reference_answer": "Apple said outsourcing manufacturing and logistics reduces its direct control and exposes it to risks involving product quality and quantity, supply availability, logistics, supplier concentration, and pricing or cost pressures.",
        "evidence": [
            {
                "document_id": "AAPL_2023_10K",
                "section_hint": "Risk Factors - Outsourcing and Suppliers",
                "evidence_text": "Apple stated that outsourcing manufacturing and logistics reduces its direct control and creates risks involving quality, quantity, supply, logistics, concentration among suppliers, and pricing."
            }
        ],
        "notes": "Qualitative supplier-dependence question."
    },
    {
        "question_id": "Q025",
        "question": "What cybersecurity risks did Microsoft discuss in its fiscal 2024 filing?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["MSFT_2024_10K"],
        "expected_tickers": ["MSFT"],
        "expected_years": [2024],
        "reference_answer": "Microsoft described cybersecurity risks from hackers and nation-state actors using malware, vulnerability exploitation, social engineering, compromised accounts and supply chains, and increasingly sophisticated attack methods. Such incidents could disrupt services, expose data, increase costs, create legal or regulatory risk, and damage Microsoft's financial condition, competitive position, and reputation.",
        "evidence": [
            {
                "document_id": "MSFT_2024_10K",
                "section_hint": "Cybersecurity, Data Privacy, and Platform Abuse Risks",
                "evidence_text": "Microsoft described attacks by hackers and nation-state actors using methods including malicious software, vulnerability exploitation, social engineering, unauthorized access, and supply-chain compromise. It stated that increasingly sophisticated cyber incidents could disrupt services, expose data, increase costs, create legal or regulatory risk, and harm its financial condition and reputation."
            }
        ],
        "notes": "Qualitative synthesis of Microsoft's cybersecurity risk discussion."
    },
    {
        "question_id": "Q026",
        "question": "What risks did NVIDIA describe from relying on third parties to manufacture its products?",
        "category": "qualitative",
        "difficulty": "medium",
        "answerable": True,
        "retrieval_scope": "company_year",
        "expected_document_ids": ["NVDA_2023_10K"],
        "expected_tickers": ["NVDA"],
        "expected_years": [2023],
        "reference_answer": "NVIDIA said relying on third-party manufacturers reduces its control over production and exposes it to risks involving manufacturing quantity, quality, yields, development, costs, and delivery schedules.",
        "evidence": [
            {
                "document_id": "NVDA_2023_10K",
                "section_hint": "Risk Factors - Third-Party Manufacturing",
                "evidence_text": "NVIDIA stated that reliance on third-party suppliers and manufacturers reduces its control over manufacturing quantity and quality, production yields, product development, costs, and delivery schedules."
            }
        ],
        "notes": "Qualitative third-party manufacturing risk question."
    }
]

with DATASET_PATH.open("a", encoding="utf-8") as f:
    for question in questions:
        f.write(json.dumps(question) + "\n")

print(f"Added {len(questions)} qualitative questions.")