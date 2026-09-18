import json
import os
import re
import sys
from pathlib import Path



from dotenv import load_dotenv

from vectorstore.azure_ai_search import AzureAISearchVectorStore


BENCHMARK_PATH = Path("evaluation/retrieval_questions.jsonl")


def normalize_text(text: str) -> str:
    """
    Normalize benchmark evidence and indexed chunk text
    so formatting differences do not dominate comparison.
    """
    text = text.lower()

    # Remove markdown formatting characters.
    text = re.sub(r"[*_#|<>]", " ", text)

    # Normalize currency spacing: "$ 391,035" -> "$391,035"
    text = re.sub(r"\$\s+", "$", text)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def extract_tokens(text: str) -> set[str]:
    """
    Extract normalized word tokens.
    """
    text = normalize_text(text)
    return set(re.findall(r"[a-z0-9]+", text))


def extract_numbers(text: str) -> set[str]:
    """
    Extract numeric values while ignoring formatting differences.

    Example:
    "$391,035" -> "391035"
    """
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", text)

    return {
        number.replace(",", "")
        for number in numbers
    }


def coverage_score(reference_text: str, chunk_text: str) -> float:
    """
    Measures how much of the reference text is represented
    inside the candidate chunk.
    """
    reference_tokens = extract_tokens(reference_text)
    chunk_tokens = extract_tokens(chunk_text)

    if not reference_tokens:
        return 0.0

    matched = reference_tokens & chunk_tokens

    return len(matched) / len(reference_tokens)


def numeric_coverage_score(
    evidence_text: str,
    chunk_text: str,
) -> float:
    """
    Financial evidence often depends heavily on exact numbers.

    Measures how many numbers from the benchmark evidence
    are present in the candidate chunk.
    """
    evidence_numbers = extract_numbers(evidence_text)

    if not evidence_numbers:
        return 1.0

    chunk_numbers = extract_numbers(chunk_text)

    matched = evidence_numbers & chunk_numbers

    return len(matched) / len(evidence_numbers)


def similarity_score(
    evidence_text: str,
    section_hint: str | None,
    chunk_text: str,
) -> float:
    """
    Deterministic candidate score for locating evidence chunks.

    This is NOT a retrieval metric.
    """

    evidence_coverage = coverage_score(
        evidence_text,
        chunk_text,
    )

    numeric_coverage = numeric_coverage_score(
        evidence_text,
        chunk_text,
    )

    section_coverage = 0.0

    if section_hint:
        section_coverage = coverage_score(
            section_hint,
            chunk_text,
        )

    return (
        0.60 * evidence_coverage
        + 0.30 * numeric_coverage
        + 0.10 * section_coverage
    )
def load_question(question_id: str) -> dict:
    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            question = json.loads(line)

            if question["question_id"] == question_id:
                return question

    raise ValueError(f"Question {question_id} not found.")


def get_chunks_for_document(
    store: AzureAISearchVectorStore,
    document_id: str,
) -> list[dict]:
    results = store.client.search(
        search_text="*",
        filter=f"document_id eq '{document_id}'",
        top=1000,
    )

    return list(results)


def main():
    load_dotenv(".env")

    store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    # Start with one question only.
    if len(sys.argv) < 2:
       raise SystemExit(
            "Usage: python -m evaluation.map_evidence_to_chunks <QUESTION_ID>"
       )

    question_id = sys.argv[1]
    question = load_question(question_id)

    print(f"\nQuestion: {question['question']}")
    print(f"Question ID: {question['question_id']}")

    for evidence_index, evidence in enumerate(
        question["evidence"],
        start=1,
    ):
        document_id = evidence["document_id"]
        evidence_text = evidence["evidence_text"]

        print("\n" + "=" * 80)
        print(f"Evidence #{evidence_index}")
        print(f"Document: {document_id}")
        print(f"Section hint: {evidence.get('section_hint')}")
        print(f"Evidence text: {evidence_text}")

        chunks = get_chunks_for_document(
            store=store,
            document_id=document_id,
        )

        print(f"\nChunks found in document: {len(chunks)}")

        candidates = []

        for chunk in chunks:
            content = chunk.get("content", "")

            score = similarity_score(
               evidence_text=evidence_text,
               section_hint=evidence.get("section_hint"),
               chunk_text=content,
            )

            candidates.append(
                {
                    "score": score,
                    "chunk_id": chunk.get("id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "content": content,
                }
            )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        print("\nTop candidate chunks:\n")

        for rank, candidate in enumerate(
            candidates[:5],
            start=1,
        ):
            print(f"Candidate rank: {rank}")
            print(f"Similarity: {candidate['score']:.4f}")
            print(f"Chunk index: {candidate['chunk_index']}")
            print(f"Chunk ID: {candidate['chunk_id']}")

            snippet = candidate["content"].replace("\n", " ")

            if len(snippet) > 500:
                snippet = snippet[:500] + "..."

            print(f"Content: {snippet}")
            print("-" * 80)


if __name__ == "__main__":
    main()