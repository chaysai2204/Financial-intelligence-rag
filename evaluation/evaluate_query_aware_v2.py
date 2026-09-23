import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

from llm.azure_openai import (
    get_embedding_client,
    get_openai_client,
)
from rag.query_aware_retriever import (
    query_aware_retrieve,
)
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)


load_dotenv()


BASELINE_PATH = Path(
    "evaluation/answer_evaluation_results.json"
)

OUTPUT_PATH = Path(
    "evaluation/query_aware_v2_results.json"
)


# Only the true RAG-oriented weak questions.
QUESTION_IDS = {
    "Q021",
    "Q022",
    "Q024",
    "Q025",
    "Q036",
    "Q038",
    "Q043",
}


FINAL_TOP_K = 5
PER_TARGET_K = 5


# =========================================================
# Load benchmark questions + original baseline results
# =========================================================


def load_questions():
    with BASELINE_PATH.open() as file:
        baseline_data = json.load(file)

    selected = []

    for result in baseline_data["results"]:

        if result["question_id"] not in QUESTION_IDS:
            continue

        selected.append(
            {
                "question_id": result["question_id"],
                "question": result["question"],
                "category": result.get("category"),
                "difficulty": result.get("difficulty"),
                "answerable": result.get(
                    "answerable",
                    True,
                ),
                "reference_answer": result.get(
                    "reference_answer"
                ),
                "baseline_answer": result["answer"],
                "baseline_evaluation": result[
                    "evaluation"
                ],
            }
        )

    return selected


# =========================================================
# Context construction
#
# V2 CHANGE:
# Explicit provenance is included in the prompt.
# =========================================================


def build_context(docs):
    blocks = []
    sources = []

    for citation_id, doc in enumerate(
        docs,
        start=1,
    ):
        metadata = doc.metadata

        company = metadata.get("company")
        ticker = metadata.get("ticker")
        year = metadata.get("year")
        document_id = metadata.get(
            "document_id"
        )

        blocks.append(
            f"[Source {citation_id}]\n"
            f"Company: {company}\n"
            f"Ticker: {ticker}\n"
            f"Fiscal Year: {year}\n"
            f"Document ID: {document_id}\n\n"
            f"{doc.page_content}"
        )

        sources.append(
            {
                "citation_id": citation_id,
                "document_id": document_id,
                "company": company,
                "ticker": ticker,
                "year": year,
                "filing_type": metadata.get(
                    "filing_type"
                ),
                "chunk_index": metadata.get(
                    "chunk_index"
                ),
                "rank": metadata.get(
                    "rank"
                ),
                "evidence": doc.page_content,
            }
        )

    return (
        "\n\n".join(blocks),
        sources,
    )


# =========================================================
# Answer generation
# =========================================================


def generate_answer(
    client,
    question,
    context,
):

    prompt = f"""
You are an expert financial analyst.

Answer the user's question using only the provided sources.

Rules:

- Cite supporting evidence using [Source N].
- Every factual claim must be supported by the provided sources.
- Use only source numbers that appear in the context.
- Do not invent citations.
- Do not use external knowledge.
- Never substitute information from a different fiscal year.
- If evidence is insufficient, clearly state that.
- When multiple companies or fiscal years appear,
  carefully attribute every fact to the company and
  fiscal year shown in the source metadata.
- Do not attribute information from one company's
  source to another company.
- For comparison questions, address every company
  requested when supporting evidence is available.

Context:
{context}

User Question:
{question}

Answer:
"""

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
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

    return {
        "answer": (
            response
            .choices[0]
            .message
            .content
        ),
        "latency_ms": latency_ms,
    }


# =========================================================
# Judge
#
# V2 CHANGE:
# Correctness and groundedness are explicitly separated.
# =========================================================


def parse_json_response(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

    return json.loads(text)


def judge_answer(
    client,
    *,
    question,
    reference_answer,
    answer,
    context,
):

    prompt = f"""
You are evaluating a financial RAG system.

This benchmark question is KNOWN TO BE ANSWERABLE.

QUESTION:
{question}

REFERENCE ANSWER:
{reference_answer}

RETRIEVED EVIDENCE:
{context}

GENERATED ANSWER:
{answer}


Evaluate CORRECTNESS separately from GROUNDEDNESS.


CORRECTNESS

2 = The generated answer correctly answers the question
    and captures the important information from the
    reference answer.

1 = The answer is partially correct but incomplete.

0 = The answer is incorrect, materially misleading,
    or fails to answer the known-answerable question.

IMPORTANT:

If the generated answer says there is insufficient
information and therefore does not answer the question,
CORRECTNESS MUST BE 0 even if the retrieved context
was actually incomplete.


GROUNDEDNESS

2 = All important factual claims are supported by
    the retrieved evidence.

1 = Mostly grounded, but contains a minor unsupported
    claim.

0 = Important claims are unsupported or contradicted
    by the retrieved evidence.

An answer may therefore be:

correctness = 0
groundedness = 2

when the retriever failed to provide enough evidence
and the model correctly abstained.


CITATION SUPPORT

2 = Citations clearly support the associated claims.

1 = Some citations are weak or incomplete.

0 = Important citations are unsupported or misleading.


Also check company attribution carefully.

If an NVIDIA source is described as Apple evidence,
or Microsoft evidence is attributed to another company,
that is an error.


Return ONLY valid JSON:

{{
  "correctness_score": 0,
  "groundedness_score": 0,
  "citation_support_score": 0,
  "correctness_reason": "",
  "groundedness_reason": "",
  "citation_reason": ""
}}
"""

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw = (
        response
        .choices[0]
        .message
        .content
    )

    try:
        return parse_json_response(raw)

    except Exception:
        return {
            "correctness_score": None,
            "groundedness_score": None,
            "citation_support_score": None,
            "correctness_reason": (
                "Could not parse judge output."
            ),
            "groundedness_reason": "",
            "citation_reason": "",
            "raw_judge_output": raw,
        }


# =========================================================
# Main experiment
# =========================================================


def main():

    questions = load_questions()

    print(
        f"Testing {len(questions)} "
        "RAG weak cases with query-aware V2."
    )

    vector_store = AzureAISearchVectorStore(
        endpoint=os.getenv(
            "AZURE_SEARCH_ENDPOINT"
        ),
        api_key=os.getenv(
            "AZURE_SEARCH_API_KEY"
        ),
        index_name=os.getenv(
            "AZURE_SEARCH_INDEX_NAME"
        ),
    )

    embeddings = get_embedding_client()

    retriever = DenseRetriever(
        vector_store.client,
        embeddings,
    )

    client = get_openai_client()

    results = []

    for index, item in enumerate(
        questions,
        start=1,
    ):

        question_id = item["question_id"]
        question = item["question"]

        print("\n" + "=" * 100)

        print(
            f"[{index}/{len(questions)}] "
            f"{question_id}"
        )

        print(question)

        # -------------------------------------------------
        # Query-aware retrieval
        # -------------------------------------------------

        retrieval_start = (
            time.perf_counter()
        )

        docs = query_aware_retrieve(
            retriever=retriever,
            question=question,
            final_top_k=FINAL_TOP_K,
            per_target_k=PER_TARGET_K,
        )

        retrieval_latency_ms = (
            time.perf_counter()
            - retrieval_start
        ) * 1000

        context, sources = build_context(
            docs
        )

        print("\nRetrieved evidence:")

        for source in sources:

            print(
                f"  Source "
                f"{source['citation_id']} | "
                f"{source['company']} | "
                f"{source['year']} | "
                f"{source['document_id']} | "
                f"chunk "
                f"{source['chunk_index']}"
            )

        # -------------------------------------------------
        # Generate answer
        # -------------------------------------------------

        generation = generate_answer(
            client=client,
            question=question,
            context=context,
        )

        answer = generation["answer"]

        print("\nGenerated answer:\n")
        print(answer)

        # -------------------------------------------------
        # Evaluate
        # -------------------------------------------------

        evaluation = judge_answer(
            client,
            question=question,
            reference_answer=item[
                "reference_answer"
            ],
            answer=answer,
            context=context,
        )

        baseline_score = (
            item[
                "baseline_evaluation"
            ]
            .get("correctness_score")
        )

        new_score = evaluation.get(
            "correctness_score"
        )

        if (
            baseline_score is not None
            and new_score is not None
        ):
            change = (
                new_score
                - baseline_score
            )
        else:
            change = None

        print(
            "\nCorrectness:",
            baseline_score,
            "→",
            new_score,
        )

        print(
            "Groundedness:",
            evaluation.get(
                "groundedness_score"
            ),
        )

        print(
            "Citation support:",
            evaluation.get(
                "citation_support_score"
            ),
        )

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------

        result = {
            "question_id": question_id,
            "question": question,
            "category": item[
                "category"
            ],
            "reference_answer": item[
                "reference_answer"
            ],

            "baseline": {
                "answer": item[
                    "baseline_answer"
                ],
                "evaluation": item[
                    "baseline_evaluation"
                ],
            },

            "query_aware_v2": {
                "answer": answer,
                "sources": sources,
                "evaluation": evaluation,
                "retrieval_latency_ms": (
                    retrieval_latency_ms
                ),
                "generation_latency_ms": (
                    generation[
                        "latency_ms"
                    ]
                ),
            },

            "correctness_change": change,
        }

        results.append(result)

        # Incremental save

        with OUTPUT_PATH.open(
            "w"
        ) as file:

            json.dump(
                {
                    "configuration": {
                        "retriever": (
                            "query_aware_dense_v2"
                        ),
                        "final_top_k": (
                            FINAL_TOP_K
                        ),
                        "per_target_k": (
                            PER_TARGET_K
                        ),
                        "explicit_source_provenance": (
                            True
                        ),
                    },
                    "results": results,
                },
                file,
                indent=2,
            )

    # =====================================================
    # Summary
    # =====================================================

    improved = 0
    unchanged = 0
    regressed = 0

    baseline_total = 0
    new_total = 0

    full_correct = 0

    for result in results:

        baseline = (
            result["baseline"]
            ["evaluation"]
            .get("correctness_score")
        )

        new = (
            result["query_aware_v2"]
            ["evaluation"]
            .get("correctness_score")
        )

        if (
            baseline is None
            or new is None
        ):
            continue

        baseline_total += baseline
        new_total += new

        if new == 2:
            full_correct += 1

        if new > baseline:
            improved += 1

        elif new == baseline:
            unchanged += 1

        else:
            regressed += 1

    summary = {
        "questions_tested": len(
            results
        ),
        "improved": improved,
        "unchanged": unchanged,
        "regressed": regressed,
        "fully_correct": full_correct,
        "baseline_correctness_total": (
            baseline_total
        ),
        "query_aware_v2_correctness_total": (
            new_total
        ),
    }

    output = {
        "configuration": {
            "retriever": (
                "query_aware_dense_v2"
            ),
            "final_top_k": FINAL_TOP_K,
            "per_target_k": PER_TARGET_K,
            "explicit_source_provenance": (
                True
            ),
        },
        "summary": summary,
        "results": results,
    }

    with OUTPUT_PATH.open(
        "w"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
        )

    print("\n" + "=" * 100)

    print(
        "QUERY-AWARE V2 "
        "EXPERIMENT COMPLETE"
    )

    print("=" * 100)

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print(
        "\nSaved to:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()