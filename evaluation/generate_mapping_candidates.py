import json
import os
from pathlib import Path

from dotenv import load_dotenv

from evaluation.map_evidence_to_chunks import (
    BENCHMARK_PATH,
    get_chunks_for_document,
    similarity_score,
)

from vectorstore.azure_ai_search import AzureAISearchVectorStore


OUTPUT_PATH = Path("evaluation/mapping_candidates.json")


def load_questions() -> list[dict]:
    questions = []

    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            questions.append(json.loads(line))

    return questions


def main():
    load_dotenv(".env")

    store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    questions = load_questions()

    output = {}

    for question in questions:

        # Unanswerable questions have no relevant evidence chunks.
        if not question["answerable"]:
            continue

        question_id = question["question_id"]

        print(f"Processing {question_id}...")

        evidence_results = []

        for evidence_index, evidence in enumerate(
            question["evidence"],
            start=1,
        ):
            document_id = evidence["document_id"]

            chunks = get_chunks_for_document(
                store=store,
                document_id=document_id,
            )

            candidates = []

            for chunk in chunks:
                content = chunk.get("content", "")

                score = similarity_score(
                    evidence_text=evidence["evidence_text"],
                    section_hint=evidence.get("section_hint"),
                    chunk_text=content,
                )

                candidates.append(
                    {
                        "chunk_id": chunk.get("id"),
                        "chunk_index": chunk.get("chunk_index"),
                        "score": round(score, 4),
                        "content": content,
                    }
                )

            candidates.sort(
                key=lambda item: item["score"],
                reverse=True,
            )

            evidence_results.append(
                {
                    "evidence_index": evidence_index,
                    "document_id": document_id,
                    "section_hint": evidence.get("section_hint"),
                    "evidence_text": evidence["evidence_text"],
                    "top_candidates": candidates[:5],
                }
            )

        output[question_id] = {
            "question": question["question"],
            "category": question["category"],
            "evidence_items": evidence_results,
        }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(f"\nCandidate mappings saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()