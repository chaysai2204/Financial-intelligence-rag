import json
import os
import time
from statistics import mean, median

import numpy as np
from dotenv import load_dotenv

from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
    HybridRetriever,
    Retriever,
)
from llm.azure_openai import get_embedding_client

BENCHMARK_PATH = "evaluation/retrieval_questions.jsonl"
MAPPING_PATH = "evaluation/evidence_chunk_map.json"

RAW_OUTPUT_PATH = "evaluation/retrieval_results.json"
SUMMARY_OUTPUT_PATH = "evaluation/retrieval_summary.json"

TOP_K = 10


def load_benchmark(path: str) -> list[dict]:
    questions = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            item = json.loads(line)

            if item.get("answerable") is True:
                questions.append(item)

    return questions


def load_mapping(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_result(result) -> dict:
    """
    Convert retriever output into a flat dictionary.

    Retriever currently returns:
        SimpleNamespace(
            page_content=...,
            metadata={
                "chunk_id": ...,
                "rank": ...,
                ...
            }
        )

    This function flattens metadata so the evaluator can use
    result["chunk_id"], result["rank"], etc.
    """

    if isinstance(result, dict):
        raw = result
    elif hasattr(result, "__dict__"):
        raw = vars(result)
    else:
        raise TypeError(
            f"Unsupported retrieval result type: {type(result)}"
        )

    metadata = raw.get("metadata", {}) or {}

    normalized = {
        **metadata,
        "content": raw.get("page_content"),
    }

    return normalized
def get_retrieved_chunk_ids(results: list[dict]) -> list[str]:
    return [
        result["chunk_id"]
        for result in results
        if result.get("chunk_id")
    ]


def evidence_item_coverage(
    retrieved_chunk_ids: list[str],
    acceptable_chunk_groups: list[list[str]],
) -> float:
    """
    For each acceptable group:
        coverage = retrieved chunks from group / total chunks in group

    Evidence-item coverage is the maximum coverage across all acceptable groups.
    """

    retrieved_set = set(retrieved_chunk_ids)

    coverages = []

    for group in acceptable_chunk_groups:
        if not group:
            continue

        matched = sum(
            1 for chunk_id in group
            if chunk_id in retrieved_set
        )

        coverage = matched / len(group)
        coverages.append(coverage)

    return max(coverages) if coverages else 0.0


def evidence_item_complete(
    retrieved_chunk_ids: list[str],
    acceptable_chunk_groups: list[list[str]],
) -> bool:
    """
    Complete if at least one acceptable group is fully retrieved.
    """

    retrieved_set = set(retrieved_chunk_ids)

    for group in acceptable_chunk_groups:
        if group and set(group).issubset(retrieved_set):
            return True

    return False


def calculate_question_metrics(
    retrieved_results: list[dict],
    mapping_entry: dict,
) -> dict:
    metrics = {}

    for k in [1, 5, 10]:
        top_k_ids = get_retrieved_chunk_ids(retrieved_results[:k])

        evidence_coverages = []
        evidence_complete_flags = []

        for evidence_item in mapping_entry["evidence_items"]:
            groups = evidence_item["acceptable_chunk_groups"]

            coverage = evidence_item_coverage(
                top_k_ids,
                groups,
            )

            complete = evidence_item_complete(
                top_k_ids,
                groups,
            )

            evidence_coverages.append(coverage)
            evidence_complete_flags.append(complete)

        question_recall = (
            mean(evidence_coverages)
            if evidence_coverages
            else 0.0
        )

        complete_success = (
            1.0
            if evidence_complete_flags
            and all(evidence_complete_flags)
            else 0.0
        )

        metrics[f"recall@{k}"] = question_recall
        metrics[f"complete_evidence@{k}"] = complete_success

    # ---------------------------------------------------------
    # MRR
    # ---------------------------------------------------------
    #
    # First rank where ANY chunk belonging to ANY acceptable
    # evidence group appears.
    #
    # This is standard first-relevant-hit MRR.
    # Complete-evidence metrics separately capture whether all
    # required evidence was retrieved.
    # ---------------------------------------------------------

    all_relevant_chunk_ids = set()

    for evidence_item in mapping_entry["evidence_items"]:
        for group in evidence_item["acceptable_chunk_groups"]:
            all_relevant_chunk_ids.update(group)

    reciprocal_rank = 0.0

    for rank, result in enumerate(retrieved_results, start=1):
        if result.get("chunk_id") in all_relevant_chunk_ids:
            reciprocal_rank = 1.0 / rank
            break

    metrics["mrr"] = reciprocal_rank

    return metrics


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0

    return float(np.percentile(values, 95))


def evaluate_strategy(
    strategy_name: str,
    retriever,
    questions: list[dict],
    mapping: dict,
) -> dict:

    print()
    print("=" * 80)
    print(f"EVALUATING: {strategy_name.upper()}")
    print("=" * 80)

    per_question = []
    latencies = []

    for index, question in enumerate(questions, start=1):

        question_id = question["question_id"]
        query = question["question"]

        if question_id not in mapping:
            print(f"[SKIP] {question_id}: no evidence mapping")
            continue

        print(
            f"[{index:02d}/{len(questions)}] "
            f"{question_id}: {query}"
        )

        start_time = time.perf_counter()

        raw_results = retriever.invoke(
          query=query,
          top_k=TOP_K,
        )
        
        results = [
           normalize_result(result)
           for result in raw_results
        ]

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        latencies.append(latency_ms)

        metrics = calculate_question_metrics(
            retrieved_results=results,
            mapping_entry=mapping[question_id],
        )

        per_question.append(
            {
                "question_id": question_id,
                "question": query,
                "category": question["category"],
                "difficulty": question["difficulty"],
                "retrieval_scope": question["retrieval_scope"],
                "latency_ms": latency_ms,
                "metrics": metrics,
                "retrieved_results": results,
            }
        )

        print(
            f"    Recall@5={metrics['recall@5']:.3f} | "
            f"Complete@5={metrics['complete_evidence@5']:.0f} | "
            f"MRR={metrics['mrr']:.3f} | "
            f"{latency_ms:.1f} ms"
        )

    summary = summarize_results(
        strategy_name=strategy_name,
        per_question=per_question,
        latencies=latencies,
    )

    return {
        "strategy": strategy_name,
        "summary": summary,
        "per_question": per_question,
    }


def summarize_results(
    strategy_name: str,
    per_question: list[dict],
    latencies: list[float],
) -> dict:

    metric_names = [
        "recall@1",
        "recall@5",
        "recall@10",
        "complete_evidence@1",
        "complete_evidence@5",
        "complete_evidence@10",
        "mrr",
    ]

    summary = {
        "strategy": strategy_name,
        "questions_evaluated": len(per_question),
    }

    for metric_name in metric_names:
        values = [
            item["metrics"][metric_name]
            for item in per_question
        ]

        summary[metric_name] = (
            mean(values)
            if values
            else 0.0
        )

    summary["latency_ms"] = {
        "mean": mean(latencies) if latencies else 0.0,
        "median": median(latencies) if latencies else 0.0,
        "p95": percentile_95(latencies),
    }

    # ---------------------------------------------------------
    # Category-level breakdown
    # ---------------------------------------------------------

    categories = sorted(
        {
            item["category"]
            for item in per_question
        }
    )

    category_metrics = {}

    for category in categories:

        category_items = [
            item
            for item in per_question
            if item["category"] == category
        ]

        category_summary = {
            "questions": len(category_items)
        }

        for metric_name in metric_names:
            values = [
                item["metrics"][metric_name]
                for item in category_items
            ]

            category_summary[metric_name] = (
                mean(values)
                if values
                else 0.0
            )

        category_metrics[category] = category_summary

    summary["by_category"] = category_metrics

    return summary


def print_summary(result: dict):
    summary = result["summary"]

    print()
    print("=" * 80)
    print(f"{result['strategy'].upper()} SUMMARY")
    print("=" * 80)

    print(
        f"Questions evaluated: "
        f"{summary['questions_evaluated']}"
    )

    print(f"Recall@1:  {summary['recall@1']:.4f}")
    print(f"Recall@5:  {summary['recall@5']:.4f}")
    print(f"Recall@10: {summary['recall@10']:.4f}")

    print(
        f"Complete Evidence@1:  "
        f"{summary['complete_evidence@1']:.4f}"
    )

    print(
        f"Complete Evidence@5:  "
        f"{summary['complete_evidence@5']:.4f}"
    )

    print(
        f"Complete Evidence@10: "
        f"{summary['complete_evidence@10']:.4f}"
    )

    print(f"MRR: {summary['mrr']:.4f}")

    latency = summary["latency_ms"]

    print()
    print("Latency")
    print(f"Mean:   {latency['mean']:.1f} ms")
    print(f"Median: {latency['median']:.1f} ms")
    print(f"P95:    {latency['p95']:.1f} ms")


def main():

    load_dotenv(".env")

    questions = load_benchmark(BENCHMARK_PATH)
    mapping = load_mapping(MAPPING_PATH)

    print("=" * 80)
    print("RETRIEVAL EVALUATION")
    print("=" * 80)

    print(f"Answerable benchmark questions: {len(questions)}")
    print(f"Mapped questions: {len(mapping)}")
    print(f"Retrieval Top-K: {TOP_K}")

    if len(questions) != 44:
        raise ValueError(
            f"Expected 44 answerable questions, got {len(questions)}"
        )

    store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    bm25_retriever = Retriever(
        client=store.client
    )

    embedding_client = get_embedding_client()

    dense_retriever = DenseRetriever(
       client=store.client,
       embeddings=embedding_client,
    )
    hybrid_retriever = HybridRetriever(
      client=store.client,
      embeddings=embedding_client,
    )  

    bm25_result = evaluate_strategy(
        strategy_name="bm25",
        retriever=bm25_retriever,
        questions=questions,
        mapping=mapping,
    )

    dense_result = evaluate_strategy(
        strategy_name="dense",
        retriever=dense_retriever,
        questions=questions,
        mapping=mapping,
    )
    hybrid_result = evaluate_strategy(
        strategy_name="hybrid",
        retriever=hybrid_retriever,
        questions=questions,
        mapping=mapping,
    )

    output = {
        "configuration": {
            "top_k": TOP_K,
            "answerable_questions": len(questions),
            "unanswerable_questions_excluded": 6,
            "retrieval_mode": "global",
        },
        "bm25": bm25_result,
        "dense": dense_result,
        "hybrid": hybrid_result,
    }

    with open(
        RAW_OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    summary_output = {
        "configuration": output["configuration"],
        "bm25": bm25_result["summary"],
        "dense": dense_result["summary"],
        "hybrid": hybrid_result["summary"],
    }

    with open(
        SUMMARY_OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary_output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print_summary(bm25_result)
    print_summary(dense_result)
    print_summary(hybrid_result)
    print()
    print("=" * 80)
    print("OUTPUT FILES")
    print("=" * 80)
    print(RAW_OUTPUT_PATH)
    print(SUMMARY_OUTPUT_PATH)
   


if __name__ == "__main__":
    main()