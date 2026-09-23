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
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)


load_dotenv()


BENCHMARK_PATH = Path(
    "evaluation/retrieval_questions.jsonl"
)

OUTPUT_PATH = Path(
    "evaluation/answer_evaluation_results.json"
)

TOP_K = 5


# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------


def load_questions():
    questions = []

    with BENCHMARK_PATH.open() as file:
        for line in file:
            if line.strip():
                questions.append(
                    json.loads(line)
                )

    return questions


# ---------------------------------------------------------
# Context construction
# ---------------------------------------------------------


def build_context(docs):
    context_blocks = []
    sources = []

    for citation_id, doc in enumerate(
        docs,
        start=1,
    ):
        metadata = doc.metadata

        context_blocks.append(
            f"[Source {citation_id}]\n"
            f"{doc.page_content}"
        )

        sources.append(
            {
                "citation_id": citation_id,
                "document_id": metadata.get(
                    "document_id"
                ),
                "company": metadata.get(
                    "company"
                ),
                "ticker": metadata.get(
                    "ticker"
                ),
                "year": metadata.get(
                    "year"
                ),
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
        "\n\n".join(context_blocks),
        sources,
    )


# ---------------------------------------------------------
# Answer generation
# ---------------------------------------------------------


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

    answer = response.choices[0].message.content

    usage = getattr(
        response,
        "usage",
        None,
    )

    return {
        "answer": answer,
        "latency_ms": latency_ms,
        "prompt_tokens": (
            getattr(
                usage,
                "prompt_tokens",
                None,
            )
            if usage
            else None
        ),
        "completion_tokens": (
            getattr(
                usage,
                "completion_tokens",
                None,
            )
            if usage
            else None
        ),
    }


# ---------------------------------------------------------
# Deterministic citation checks
# ---------------------------------------------------------


def extract_citations(answer):
    citations = re.findall(
        r"\[Source\s+(\d+)\]",
        answer,
        flags=re.IGNORECASE,
    )

    return [
        int(value)
        for value in citations
    ]


def check_citation_syntax(
    answer,
    source_count,
):
    citation_ids = extract_citations(
        answer
    )

    invalid = [
        citation_id
        for citation_id in citation_ids
        if citation_id < 1
        or citation_id > source_count
    ]

    return {
        "citation_ids": citation_ids,
        "has_citations": (
            len(citation_ids) > 0
        ),
        "invalid_citations": invalid,
        "citation_ids_valid": (
            len(invalid) == 0
        ),
    }


# ---------------------------------------------------------
# LLM judge
# ---------------------------------------------------------


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
    answer,
    reference_answer,
    answerable,
    context,
):
    judge_prompt = f"""
You are evaluating a financial RAG system.

Evaluate the generated answer objectively.

QUESTION:
{question}

EXPECTED ANSWERABLE:
{answerable}

REFERENCE ANSWER:
{reference_answer}

RETRIEVED EVIDENCE:
{context}

GENERATED ANSWER:
{answer}

Scoring rubric:

CORRECTNESS SCORE
2 = correct and captures the important information in the reference answer
1 = partially correct but incomplete or contains a minor issue
0 = incorrect, materially misleading, or fails to answer an answerable question

GROUNDEDNESS SCORE
2 = factual claims are supported by the retrieved evidence
1 = mostly grounded but contains a minor unsupported claim
0 = important claims are unsupported or contradicted by the evidence

CITATION SUPPORT SCORE
2 = citations clearly support the claims they are attached to
1 = citations are partially appropriate or some claims are poorly cited
0 = citations do not support important claims or citations are misleading

ABSTENTION SCORE
For an unanswerable question:
2 = correctly states that there is insufficient information
0 = attempts to provide an unsupported answer

For an answerable question:
use null.

Important:
- Do not reward verbosity.
- Do not penalize different wording if the meaning is correct.
- Do not require every detail from the reference answer if the user's question is adequately answered.
- Judge grounding only from RETRIEVED EVIDENCE.
- A fact may be true in the real world but still be ungrounded here.
- Do not assume facts that are not shown.

Return ONLY valid JSON:

{{
  "correctness_score": 0,
  "groundedness_score": 0,
  "citation_support_score": 0,
  "abstention_score": null,
  "correctness_reason": "",
  "groundedness_reason": "",
  "citation_reason": "",
  "abstention_reason": ""
}}
"""

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
        messages=[
            {
                "role": "user",
                "content": judge_prompt,
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
        return parse_json_response(
            raw
        )

    except Exception:
        return {
            "correctness_score": None,
            "groundedness_score": None,
            "citation_support_score": None,
            "abstention_score": None,
            "correctness_reason": (
                "Judge output could not "
                "be parsed."
            ),
            "groundedness_reason": "",
            "citation_reason": "",
            "abstention_reason": "",
            "raw_judge_output": raw,
        }


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------


def average_score(
    results,
    key,
):
    values = [
        result["evaluation"].get(key)
        for result in results
        if result["evaluation"].get(key)
        is not None
    ]

    if not values:
        return None

    return sum(values) / len(values)


def calculate_summary(results):
    answerable_results = [
        result
        for result in results
        if result["answerable"]
    ]

    unanswerable_results = [
        result
        for result in results
        if not result["answerable"]
    ]

    valid_citation_cases = sum(
        1
        for result in results
        if result[
            "citation_check"
        ]["citation_ids_valid"]
    )

    summary = {
        "total_questions": len(results),
        "answerable_questions": len(
            answerable_results
        ),
        "unanswerable_questions": len(
            unanswerable_results
        ),
        "average_correctness_score": (
            average_score(
                answerable_results,
                "correctness_score",
            )
        ),
        "average_groundedness_score": (
            average_score(
                results,
                "groundedness_score",
            )
        ),
        "average_citation_support_score": (
            average_score(
                answerable_results,
                "citation_support_score",
            )
        ),
        "average_abstention_score": (
            average_score(
                unanswerable_results,
                "abstention_score",
            )
        ),
        "valid_citation_id_rate": (
            valid_citation_cases
            / len(results)
            if results
            else 0
        ),
    }

    return summary


# ---------------------------------------------------------
# Main experiment
# ---------------------------------------------------------


def main():
    questions = load_questions()

    print(
        f"Loaded {len(questions)} "
        "benchmark questions."
    )

    vector_store = (
        AzureAISearchVectorStore(
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
    )

    embeddings = (
        get_embedding_client()
    )

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
        question_id = item[
            "question_id"
        ]

        question = item[
            "question"
        ]

        answerable = item.get(
            "answerable",
            True,
        )

        reference_answer = item.get(
            "reference_answer"
        )

        print(
            "\n"
            + "=" * 90
        )

        print(
            f"[{index}/{len(questions)}] "
            f"{question_id}"
        )

        print(question)

        # -----------------------------
        # Retrieval
        # -----------------------------

        retrieval_start = (
            time.perf_counter()
        )

        docs = retriever.invoke(
            query=question,
            top_k=TOP_K,
        )

        retrieval_latency_ms = (
            time.perf_counter()
            - retrieval_start
        ) * 1000

        context, sources = (
            build_context(docs)
        )

        # -----------------------------
        # Generation
        # -----------------------------

        generation = (
            generate_answer(
                client=client,
                question=question,
                context=context,
            )
        )

        answer = generation[
            "answer"
        ]

        print("\nAnswer:")
        print(answer)

        # -----------------------------
        # Citation validation
        # -----------------------------

        citation_check = (
            check_citation_syntax(
                answer,
                len(sources),
            )
        )

        # -----------------------------
        # LLM evaluation
        # -----------------------------

        evaluation = judge_answer(
            client,
            question=question,
            answer=answer,
            reference_answer=(
                reference_answer
            ),
            answerable=answerable,
            context=context,
        )

        print(
            "\nScores:",
            f"correctness="
            f"{evaluation.get('correctness_score')}",
            f"groundedness="
            f"{evaluation.get('groundedness_score')}",
            f"citations="
            f"{evaluation.get('citation_support_score')}",
            f"abstention="
            f"{evaluation.get('abstention_score')}",
        )

        result = {
            "question_id": question_id,
            "question": question,
            "category": item.get(
                "category"
            ),
            "difficulty": item.get(
                "difficulty"
            ),
            "answerable": answerable,
            "reference_answer": (
                reference_answer
            ),
            "answer": answer,
            "sources": sources,
            "citation_check": (
                citation_check
            ),
            "evaluation": evaluation,
            "retrieval_latency_ms": (
                retrieval_latency_ms
            ),
            "generation_latency_ms": (
                generation[
                    "latency_ms"
                ]
            ),
            "prompt_tokens": (
                generation[
                    "prompt_tokens"
                ]
            ),
            "completion_tokens": (
                generation[
                    "completion_tokens"
                ]
            ),
        }

        results.append(result)

        # Save incrementally so progress
        # is not lost if a later request fails.
        with OUTPUT_PATH.open(
            "w"
        ) as file:
            json.dump(
                {
                    "configuration": {
                        "retriever": "dense",
                        "top_k": TOP_K,
                        "chunking": (
                            "recursive_markdown_aware"
                        ),
                    },
                    "results": results,
                },
                file,
                indent=2,
            )

    summary = calculate_summary(
        results
    )

    output = {
        "configuration": {
            "retriever": "dense",
            "top_k": TOP_K,
            "chunking": (
                "recursive_markdown_aware"
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

    print(
        "\n"
        + "=" * 90
    )

    print(
        "ANSWER EVALUATION COMPLETE"
    )

    print(
        "=" * 90
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()