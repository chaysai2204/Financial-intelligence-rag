import json
import os
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from llm.azure_openai import (
    get_embedding_client,
    get_openai_client,
)
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)

load_dotenv()


BENCHMARK_PATH = Path("evaluation/retrieval_questions.jsonl")
OUTPUT_PATH = Path("evaluation/context_k_experiment_results.json")

TOP_K_VALUES = [5, 10]

QUESTIONS_PER_CATEGORY = 3

CATEGORIES = [
    "factual",
    "paraphrase",
    "qualitative",
    "temporal",
    "cross_company",
    "evidence_seeking",
]


def load_questions():
    questions = []

    with BENCHMARK_PATH.open("r") as file:
        for line in file:
            if line.strip():
                questions.append(json.loads(line))

    return questions


def select_questions(questions):
    """
    Select a deterministic 18-question subset:
    3 answerable questions from each supported category.
    """

    grouped = defaultdict(list)

    for question in questions:
        if not question.get("answerable", False):
            continue

        category = question.get("category")

        if category in CATEGORIES:
            grouped[category].append(question)

    selected = []

    for category in CATEGORIES:
        category_questions = sorted(
            grouped[category],
            key=lambda item: item["question_id"],
        )

        selected.extend(
            category_questions[:QUESTIONS_PER_CATEGORY]
        )

    return selected


def build_context(docs):
    context_blocks = []
    sources = []

    for citation_id, doc in enumerate(docs, start=1):
        metadata = doc.metadata

        context_blocks.append(
            f"[Source {citation_id}]\n"
            f"{doc.page_content}"
        )

        sources.append(
            {
                "citation_id": citation_id,
                "document_id": metadata.get("document_id"),
                "company": metadata.get("company"),
                "ticker": metadata.get("ticker"),
                "year": metadata.get("year"),
                "filing_type": metadata.get("filing_type"),
                "chunk_index": metadata.get("chunk_index"),
                "rank": metadata.get("rank"),
            }
        )

    return "\n\n".join(context_blocks), sources


def generate_answer(
    client,
    question,
    context,
):
    prompt = f"""
You are an expert financial analyst.

Answer the user's question using only the provided sources.

Citation rules:
- Cite the supporting source using [Source N].
- Every factual claim must be supported by at least one source.
- Use only source numbers that appear in the provided context.
- Do not invent citations.
- If the provided sources do not contain enough evidence to answer the question, say that you do not have enough information.
- When abstaining, do not cite unrelated sources as if they support the missing answer.
- Never substitute data from a different fiscal year for the year requested.

Context:
{context}

User Question:
{question}

Answer:
"""

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    answer = response.choices[0].message.content

    usage = getattr(response, "usage", None)

    prompt_tokens = (
        getattr(usage, "prompt_tokens", None)
        if usage
        else None
    )

    completion_tokens = (
        getattr(usage, "completion_tokens", None)
        if usage
        else None
    )

    return {
        "answer": answer,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "context_chars": len(context),
    }


def run_experiment():
    questions = load_questions()
    selected_questions = select_questions(questions)

    print(
        f"Selected {len(selected_questions)} questions "
        f"for K=5 vs K=10 experiment."
    )

    vector_store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    embeddings = get_embedding_client()

    retriever = DenseRetriever(
        vector_store.client,
        embeddings,
    )

    client = get_openai_client()

    results = []

    for index, item in enumerate(
        selected_questions,
        start=1,
    ):
        question_id = item["question_id"]
        question = item["question"]
        category = item["category"]

        print("\n" + "=" * 100)
        print(
            f"[{index}/{len(selected_questions)}] "
            f"{question_id} | {category}"
        )
        print(question)
        print("=" * 100)

        question_result = {
            "question_id": question_id,
            "question": question,
            "category": category,
            "difficulty": item.get("difficulty"),
            "reference_answer": item.get(
                "reference_answer"
            ),
            "runs": {},
        }

        for top_k in TOP_K_VALUES:
            print(f"\nRunning K={top_k}...")

            retrieval_start = time.perf_counter()

            docs = retriever.invoke(
                query=question,
                top_k=top_k,
            )

            retrieval_latency_ms = (
                time.perf_counter()
                - retrieval_start
            ) * 1000

            context, sources = build_context(docs)

            generation = generate_answer(
                client=client,
                question=question,
                context=context,
            )

            question_result["runs"][str(top_k)] = {
                "answer": generation["answer"],
                "sources": sources,
                "retrieval_latency_ms": (
                    retrieval_latency_ms
                ),
                "generation_latency_ms": (
                    generation["latency_ms"]
                ),
                "total_latency_ms": (
                    retrieval_latency_ms
                    + generation["latency_ms"]
                ),
                "context_chars": (
                    generation["context_chars"]
                ),
                "prompt_tokens": (
                    generation["prompt_tokens"]
                ),
                "completion_tokens": (
                    generation["completion_tokens"]
                ),
            }

            print(
                f"K={top_k} | "
                f"retrieval={retrieval_latency_ms:.1f} ms | "
                f"generation={generation['latency_ms']:.1f} ms | "
                f"context_chars={generation['context_chars']} | "
                f"prompt_tokens={generation['prompt_tokens']}"
            )

        results.append(question_result)

    output = {
        "experiment": {
            "retriever": "dense",
            "chunking": "recursive_markdown_aware",
            "top_k_values": TOP_K_VALUES,
            "questions_per_category": (
                QUESTIONS_PER_CATEGORY
            ),
            "question_count": len(
                selected_questions
            ),
        },
        "results": results,
    }

    with OUTPUT_PATH.open("w") as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print("\n" + "=" * 100)
    print("EXPERIMENT COMPLETE")
    print("=" * 100)
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_experiment()