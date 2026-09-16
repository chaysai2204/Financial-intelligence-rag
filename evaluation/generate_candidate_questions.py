import json
from pathlib import Path


OUTPUT_PATH = Path("evaluation/candidate_questions.jsonl")


questions = [
    # ---------- FACTUAL ----------
    ("Q006", "What were Apple's Services net sales in fiscal 2024?", "factual", "easy", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),
    ("Q007", "What were Apple's total net sales in fiscal 2023?", "factual", "easy", "company_year", ["AAPL_2023_10K"], ["AAPL"], [2023]),
    ("Q008", "What was Microsoft's total revenue in fiscal 2024?", "factual", "easy", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q009", "What was Microsoft's total revenue in fiscal 2023?", "factual", "easy", "company_year", ["MSFT_2023_10K"], ["MSFT"], [2023]),
    ("Q010", "What was NVIDIA's total revenue in fiscal 2023?", "factual", "easy", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q011", "What was Apple's net income in fiscal 2024?", "factual", "easy", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),
    ("Q012", "What was Microsoft's net income in fiscal 2024?", "factual", "easy", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q013", "How much revenue did NVIDIA generate from its Data Center business in fiscal 2023?", "factual", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q014", "What were Apple's iPhone net sales in fiscal 2023?", "factual", "easy", "company_year", ["AAPL_2023_10K"], ["AAPL"], [2023]),

    # ---------- PARAPHRASE ----------
    ("Q015", "How much profit did Apple keep after all expenses in fiscal 2024?", "paraphrase", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),
    ("Q016", "How much money did Microsoft bring in from its business operations in fiscal 2024?", "paraphrase", "medium", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q017", "How much did NVIDIA earn from sales during fiscal 2023?", "paraphrase", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q018", "How much did Apple make from its services business during fiscal 2023?", "paraphrase", "medium", "company_year", ["AAPL_2023_10K"], ["AAPL"], [2023]),
    ("Q019", "How much profit remained for Microsoft shareholders in fiscal 2023?", "paraphrase", "medium", "company_year", ["MSFT_2023_10K"], ["MSFT"], [2023]),
    ("Q020", "How much money did Apple generate from iPhone sales during fiscal 2024?", "paraphrase", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),

    # ---------- QUALITATIVE ----------
    ("Q021", "What factors did Apple identify as risks to its global supply chain?", "qualitative", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),
    ("Q022", "What competitive pressures did Microsoft identify in its fiscal 2024 filing?", "qualitative", "medium", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q023", "What factors could make it difficult for NVIDIA to accurately forecast demand?", "qualitative", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q024", "What risks did Apple describe related to dependence on third-party suppliers?", "qualitative", "medium", "company_year", ["AAPL_2023_10K"], ["AAPL"], [2023]),
    ("Q025", "What cybersecurity risks did Microsoft discuss in its fiscal 2024 filing?", "qualitative", "medium", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q026", "What risks did NVIDIA describe from relying on third parties to manufacture its products?", "qualitative", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),

    # ---------- TEMPORAL ----------
    ("Q027", "How did Apple's Services net sales change from fiscal 2023 to fiscal 2024?", "temporal", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2023, 2024]),
    ("Q028", "How did Apple's net income change from fiscal 2023 to fiscal 2024?", "temporal", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2023, 2024]),
    ("Q029", "How did Microsoft's total revenue change from fiscal 2023 to fiscal 2024?", "temporal", "medium", "temporal", ["MSFT_2023_10K", "MSFT_2024_10K"], ["MSFT"], [2023, 2024]),
    ("Q030", "How did Microsoft's net income change from fiscal 2023 to fiscal 2024?", "temporal", "medium", "temporal", ["MSFT_2023_10K", "MSFT_2024_10K"], ["MSFT"], [2023, 2024]),
    ("Q031", "How did Apple's iPhone net sales change between fiscal 2023 and fiscal 2024?", "temporal", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2023, 2024]),
    ("Q032", "How did Apple's Services contribution to total net sales change from fiscal 2023 to fiscal 2024?", "temporal", "hard", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2023, 2024]),

    # ---------- CROSS-COMPANY ----------
    ("Q033", "How did Apple's fiscal 2024 revenue compare with Microsoft's fiscal 2024 revenue?", "cross_company", "medium", "cross_company", ["AAPL_2024_10K", "MSFT_2024_10K"], ["AAPL", "MSFT"], [2024]),
    ("Q034", "How did Apple's fiscal 2024 net income compare with Microsoft's fiscal 2024 net income?", "cross_company", "medium", "cross_company", ["AAPL_2024_10K", "MSFT_2024_10K"], ["AAPL", "MSFT"], [2024]),
    ("Q035", "Which supply-chain risks were discussed by both Apple and NVIDIA?", "cross_company", "hard", "cross_company", ["AAPL_2023_10K", "NVDA_2023_10K"], ["AAPL", "NVDA"], [2023]),
    ("Q036", "How did Apple and Microsoft describe competitive pressures in their fiscal 2024 filings?", "cross_company", "hard", "cross_company", ["AAPL_2024_10K", "MSFT_2024_10K"], ["AAPL", "MSFT"], [2024]),
    ("Q037", "How did Apple's fiscal 2023 revenue compare with Microsoft's fiscal 2023 revenue?", "cross_company", "medium", "cross_company", ["AAPL_2023_10K", "MSFT_2023_10K"], ["AAPL", "MSFT"], [2023]),
    ("Q038", "How did Apple and NVIDIA describe risks arising from third-party manufacturing relationships?", "cross_company", "hard", "cross_company", ["AAPL_2023_10K", "NVDA_2023_10K"], ["AAPL", "NVDA"], [2023]),
    ("Q039", "How did Apple's fiscal 2023 net income compare with Microsoft's fiscal 2023 net income?", "cross_company", "medium", "cross_company", ["AAPL_2023_10K", "MSFT_2023_10K"], ["AAPL", "MSFT"], [2023]),

    # ---------- EVIDENCE SEEKING ----------
    ("Q040", "What evidence does Apple provide about the importance of Services to its fiscal 2024 sales?", "evidence_seeking", "medium", "company_year", ["AAPL_2024_10K"], ["AAPL"], [2024]),
    ("Q041", "What evidence does Microsoft provide about the performance of its cloud business in fiscal 2024?", "evidence_seeking", "medium", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),
    ("Q042", "What evidence does NVIDIA provide that it relies heavily on external manufacturing partners?", "evidence_seeking", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q043", "What evidence does Apple provide that international markets are important to its business?", "evidence_seeking", "medium", "company_year", ["AAPL_2023_10K"], ["AAPL"], [2023]),
    ("Q044", "What evidence does NVIDIA provide that demand forecasting can affect its financial performance?", "evidence_seeking", "medium", "company_year", ["NVDA_2023_10K"], ["NVDA"], [2023]),
    ("Q045", "What evidence does Microsoft provide about the importance of cloud services to its business?", "evidence_seeking", "medium", "company_year", ["MSFT_2024_10K"], ["MSFT"], [2024]),

    # ---------- UNANSWERABLE ----------
    ("Q046", "What was Microsoft's total revenue in fiscal 2025?", "unanswerable", "easy", "company_year", [], ["MSFT"], [2025]),
    ("Q047", "What was NVIDIA's total revenue in fiscal 2024?", "unanswerable", "easy", "company_year", [], ["NVDA"], [2024]),
    ("Q048", "How much revenue did Apple generate in fiscal 2026?", "unanswerable", "easy", "company_year", [], ["AAPL"], [2026]),
    ("Q049", "What was NVIDIA's net income in fiscal 2025?", "unanswerable", "easy", "company_year", [], ["NVDA"], [2025]),
    ("Q050", "How did Microsoft's revenue change from fiscal 2024 to fiscal 2025?", "unanswerable", "medium", "temporal", [], ["MSFT"], [2024, 2025]),
]


def main():
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for (
            question_id,
            question,
            category,
            difficulty,
            retrieval_scope,
            document_ids,
            tickers,
            years,
        ) in questions:

            answerable = category != "unanswerable"

            record = {
                "question_id": question_id,
                "question": question,
                "category": category,
                "difficulty": difficulty,
                "answerable": answerable,
                "retrieval_scope": retrieval_scope,
                "expected_document_ids": document_ids,
                "expected_tickers": tickers,
                "expected_years": years,
                "reference_answer": None,
                "evidence": [],
                "notes": "Candidate question pending human evidence verification."
                if answerable
                else "Required filing/year is not available in the live benchmark corpus. System should abstain.",
            }

            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Generated {len(questions)} candidate questions.")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()