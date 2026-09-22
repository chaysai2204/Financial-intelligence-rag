import json
import os
from pathlib import Path

from dotenv import load_dotenv

from llm.azure_openai import get_embedding_client
from rag.kpi_extractor_rag import extract_financial_metrics
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)

load_dotenv()

KPI_FIELDS = [
    "revenue",
    "net_income",
    "operating_income",
    "cash_flow",
    "total_assets",
    "total_liabilities",
]

GROUND_TRUTH_PATH = Path("evaluation/kpi_ground_truth.json")


def normalize_financial_value(value):
    """
    Normalize financial values to millions.

    Examples:
        "$ 391,035"        -> 391035
        "391,035"          -> 391035
        "391035"           -> 391035
        "$391.035 billion" -> 391035
        None               -> None
    """

    if value is None:
        return None

    text = str(value).strip().lower()

    is_billion = "billion" in text

    text = (
        text.replace("$", "")
        .replace(",", "")
        .replace("million", "")
        .replace("billions", "")
        .replace("billion", "")
        .strip()
    )

    try:
        number = float(text)
    except ValueError:
        return None

    if is_billion:
        number *= 1000

    if number.is_integer():
        return int(number)

    return number


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r") as file:
        return json.load(file)


def build_retriever():
    vector_store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    embeddings = get_embedding_client()

    return DenseRetriever(
        client=vector_store.client,
        embeddings=embeddings,
    )


def evaluate_document(
    retriever,
    document_id,
    document_data,
):
    company = document_data["company"]
    year = document_data["fiscal_year"]
    expected_metrics = document_data["metrics"]

    print("\n" + "=" * 100)
    print(f"Evaluating: {document_id}")
    print(f"Company: {company}")
    print(f"Fiscal Year: {year}")
    print("=" * 100)

    predictions = extract_financial_metrics(
        retriever=retriever,
        company=company,
        year=year,
    )

    results = []

    for field in KPI_FIELDS:
        expected_raw = expected_metrics.get(field)
        predicted_raw = predictions.get(field)

        expected = normalize_financial_value(expected_raw)
        predicted = normalize_financial_value(predicted_raw)

        if predicted is None:
            status = "missing"
        elif predicted == expected:
            status = "correct"
        else:
            status = "incorrect"

        results.append(
            {
                "document_id": document_id,
                "company": company,
                "fiscal_year": year,
                "kpi": field,
                "expected_raw": expected_raw,
                "predicted_raw": predicted_raw,
                "expected_normalized": expected,
                "predicted_normalized": predicted,
                "status": status,
            }
        )

        print(
            f"{field:20} | "
            f"expected={expected} | "
            f"predicted={predicted} | "
            f"{status.upper()}"
        )

    return results


def build_summary(results):
    total = len(results)
    correct = sum(1 for item in results if item["status"] == "correct")
    incorrect = sum(1 for item in results if item["status"] == "incorrect")
    missing = sum(1 for item in results if item["status"] == "missing")

    accuracy = correct / total if total else 0
    incorrect_rate = incorrect / total if total else 0
    missing_rate = missing / total if total else 0

    per_kpi = {}

    for field in KPI_FIELDS:
        field_results = [
            item for item in results
            if item["kpi"] == field
        ]

        field_total = len(field_results)
        field_correct = sum(
            1 for item in field_results
            if item["status"] == "correct"
        )

        per_kpi[field] = {
            "total": field_total,
            "correct": field_correct,
            "accuracy": (
                field_correct / field_total
                if field_total
                else 0
            ),
        }

    per_company = {}

    companies = sorted(
        set(item["company"] for item in results)
    )

    for company in companies:
        company_results = [
            item for item in results
            if item["company"] == company
        ]

        company_total = len(company_results)
        company_correct = sum(
            1 for item in company_results
            if item["status"] == "correct"
        )

        per_company[company] = {
            "total": company_total,
            "correct": company_correct,
            "accuracy": (
                company_correct / company_total
                if company_total
                else 0
            ),
        }

    return {
        "total_cases": total,
        "correct": correct,
        "incorrect": incorrect,
        "missing": missing,
        "accuracy": accuracy,
        "incorrect_rate": incorrect_rate,
        "missing_rate": missing_rate,
        "per_kpi": per_kpi,
        "per_company": per_company,
    }


def main():
    ground_truth = load_ground_truth()
    retriever = build_retriever()

    all_results = []

    for document_id, document_data in ground_truth.items():
        document_results = evaluate_document(
            retriever=retriever,
            document_id=document_id,
            document_data=document_data,
        )

        all_results.extend(document_results)

    summary = build_summary(all_results)

    print("\n" + "=" * 100)
    print("KPI EXTRACTION SUMMARY")
    print("=" * 100)

    print(f"Total cases:    {summary['total_cases']}")
    print(f"Correct:        {summary['correct']}")
    print(f"Incorrect:      {summary['incorrect']}")
    print(f"Missing:        {summary['missing']}")
    print(f"Accuracy:       {summary['accuracy']:.4f}")
    print(f"Incorrect rate: {summary['incorrect_rate']:.4f}")
    print(f"Missing rate:   {summary['missing_rate']:.4f}")

    output = {
        "results": all_results,
        "summary": summary,
    }

    output_path = Path(
        "evaluation/kpi_extraction_results.json"
    )

    with open(output_path, "w") as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print(f"\nSaved results to: {output_path}")


if __name__ == "__main__":
    main()