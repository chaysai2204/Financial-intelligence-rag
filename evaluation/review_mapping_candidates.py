import json
import sys
from pathlib import Path


CANDIDATES_PATH = Path("evaluation/mapping_candidates.json")


def load_candidates() -> dict:
    with CANDIDATES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python -m evaluation.review_mapping_candidates <QUESTION_ID>"
        )

    question_id = sys.argv[1]

    data = load_candidates()

    if question_id not in data:
        raise ValueError(
            f"{question_id} not found in mapping candidates."
        )

    question = data[question_id]

    print("\n" + "=" * 100)
    print(f"Question ID: {question_id}")
    print(f"Question: {question['question']}")
    print(f"Category: {question['category']}")
    print("=" * 100)

    for evidence in question["evidence_items"]:
        print("\n" + "-" * 100)
        print(f"Evidence #{evidence['evidence_index']}")
        print(f"Document: {evidence['document_id']}")
        print(f"Section hint: {evidence['section_hint']}")
        print(f"Evidence text: {evidence['evidence_text']}")
        print("-" * 100)

        for rank, candidate in enumerate(
            evidence["top_candidates"],
            start=1,
        ):
            print(f"\nCandidate rank: {rank}")
            print(f"Score: {candidate['score']}")
            print(f"Chunk index: {candidate['chunk_index']}")
            print(f"Chunk ID: {candidate['chunk_id']}")
            print("\nFULL CONTENT:\n")
            print(candidate["content"])
            print("\n" + "." * 100)


if __name__ == "__main__":
    main()