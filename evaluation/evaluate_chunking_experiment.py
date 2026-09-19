import json
import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from llm.azure_openai import get_embedding_client
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)


load_dotenv(dotenv_path=".env")


BENCHMARK_FILE = Path(
    "evaluation/retrieval_questions.jsonl"
)

BASELINE_MAP_FILE = Path(
    "evaluation/evidence_chunk_map.json"
)

STRUCTURAL_MAP_FILE = Path(
    "evaluation/evidence_chunk_map_structural.json"
)

BASELINE_INDEX = "financial-documents-v2"
STRUCTURAL_INDEX = "financial-documents-structural-v2"

TARGET_DOCUMENT = "AAPL_2024_10K"
TOP_K = 10

OUTPUT_FILE = Path(
    "evaluation/chunking_experiment_results.json"
)


def load_questions():
    questions = []

    with BENCHMARK_FILE.open(
        encoding="utf-8"
    ) as file:

        for line in file:
            q = json.loads(line)

            if not q.get("answerable", False):
                continue

            expected_docs = set(
                q.get(
                    "expected_document_ids",
                    []
                )
            )

            if expected_docs == {
                TARGET_DOCUMENT
            }:
                questions.append(q)

    return questions


def load_mapping(path):
    with path.open(
        encoding="utf-8"
    ) as file:
        return json.load(file)


def normalize_result(result):
    metadata = result.metadata

    return {
        "chunk_id": metadata.get(
            "chunk_id"
        ),
        "rank": metadata.get(
            "rank"
        ),
        "score": metadata.get(
            "score"
        ),
        "document_id": metadata.get(
            "document_id"
        ),
    }


def evidence_item_coverage(
    retrieved_ids,
    acceptable_groups,
):
    best = 0.0

    for group in acceptable_groups:
        matched = len(
            set(group)
            & set(retrieved_ids)
        )

        coverage = (
            matched / len(group)
            if group
            else 0.0
        )

        best = max(
            best,
            coverage
        )

    return best


def evidence_item_complete(
    retrieved_ids,
    acceptable_groups,
):
    retrieved_set = set(
        retrieved_ids
    )

    for group in acceptable_groups:
        if set(group).issubset(
            retrieved_set
        ):
            return True

    return False


def calculate_metrics(
    retrieved_ids,
    question_mapping,
):
    evidence_items = (
        question_mapping[
            "evidence_items"
        ]
    )

    recalls = {}

    completes = {}

    for k in [1, 5, 10]:

        top_ids = retrieved_ids[:k]

        coverages = []

        item_completes = []

        for item in evidence_items:
            groups = item[
                "acceptable_chunk_groups"
            ]

            coverages.append(
                evidence_item_coverage(
                    top_ids,
                    groups,
                )
            )

            item_completes.append(
                evidence_item_complete(
                    top_ids,
                    groups,
                )
            )

        recalls[f"recall@{k}"] = (
            sum(coverages)
            / len(coverages)
        )

        completes[
            f"complete@{k}"
        ] = int(
            all(item_completes)
        )

    relevant_ids = set()

    for item in evidence_items:
        for group in item[
            "acceptable_chunk_groups"
        ]:
            relevant_ids.update(group)

    mrr = 0.0

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant_ids:
            mrr = 1.0 / rank
            break

    return {
        **recalls,
        **completes,
        "mrr": mrr,
    }


def evaluate_strategy(
    name,
    retriever,
    questions,
    mapping,
):
    results = []

    for q in questions:
        qid = q["question_id"]

        start = time.perf_counter()

        retrieved = retriever.invoke(
            q["question"],
            top_k=TOP_K,
        )

        latency_ms = (
            time.perf_counter()
            - start
        ) * 1000

        normalized = [
            normalize_result(r)
            for r in retrieved
        ]

        retrieved_ids = [
            r["chunk_id"]
            for r in normalized
        ]

        metrics = calculate_metrics(
            retrieved_ids,
            mapping[qid],
        )

        results.append(
            {
                "question_id": qid,
                "category":
                    q["category"],
                "question":
                    q["question"],
                "latency_ms":
                    latency_ms,
                "metrics":
                    metrics,
                "results":
                    normalized,
            }
        )

        print(
            name,
            qid,
            f"R@5={metrics['recall@5']:.3f}",
            f"MRR={metrics['mrr']:.3f}",
        )

    return results


def summarize(results):
    def avg(metric):
        return sum(
            r["metrics"][metric]
            for r in results
        ) / len(results)

    latencies = [
        r["latency_ms"]
        for r in results
    ]

    return {
        "questions": len(results),
        "recall@1":
            avg("recall@1"),
        "recall@5":
            avg("recall@5"),
        "recall@10":
            avg("recall@10"),
        "complete@1":
            avg("complete@1"),
        "complete@5":
            avg("complete@5"),
        "complete@10":
            avg("complete@10"),
        "mrr":
            avg("mrr"),
        "latency_mean_ms":
            statistics.mean(
                latencies
            ),
        "latency_median_ms":
            statistics.median(
                latencies
            ),
    }


def main():
    questions = load_questions()

    baseline_map = load_mapping(
        BASELINE_MAP_FILE
    )

    structural_map = load_mapping(
        STRUCTURAL_MAP_FILE
    )

    print(
        "Questions:",
        len(questions)
    )

    embeddings = (
        get_embedding_client()
    )

    baseline_store = (
        AzureAISearchVectorStore(
            endpoint=os.getenv(
                "AZURE_SEARCH_ENDPOINT"
            ),
            api_key=os.getenv(
                "AZURE_SEARCH_API_KEY"
            ),
            index_name=BASELINE_INDEX,
        )
    )

    structural_store = (
        AzureAISearchVectorStore(
            endpoint=os.getenv(
                "AZURE_SEARCH_ENDPOINT"
            ),
            api_key=os.getenv(
                "AZURE_SEARCH_API_KEY"
            ),
            index_name=STRUCTURAL_INDEX,
        )
    )

    baseline_retriever = (
        DenseRetriever(
            baseline_store.client,
            embeddings,
        )
    )

    structural_retriever = (
        DenseRetriever(
            structural_store.client,
            embeddings,
        )
    )

    print(
        "\nEvaluating recursive baseline..."
    )

    baseline_results = (
        evaluate_strategy(
            "Recursive",
            baseline_retriever,
            questions,
            baseline_map,
        )
    )

    print(
        "\nEvaluating Structural v2..."
    )

    structural_results = (
        evaluate_strategy(
            "Structural",
            structural_retriever,
            questions,
            structural_map,
        )
    )

    output = {
        "experiment": {
            "document":
                TARGET_DOCUMENT,
            "questions":
                len(questions),
            "top_k":
                TOP_K,
        },
        "recursive": {
            "summary":
                summarize(
                    baseline_results
                ),
            "results":
                baseline_results,
        },
        "structural_v2": {
            "summary":
                summarize(
                    structural_results
                ),
            "results":
                structural_results,
        },
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\nRecursive")
    print(
        json.dumps(
            output["recursive"][
                "summary"
            ],
            indent=2,
        )
    )

    print("\nStructural v2")
    print(
        json.dumps(
            output["structural_v2"][
                "summary"
            ],
            indent=2,
        )
    )

    print(
        f"\nWrote results to "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()