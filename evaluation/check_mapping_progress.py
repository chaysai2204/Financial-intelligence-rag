import json
from pathlib import Path


BENCHMARK_PATH = Path("evaluation/retrieval_questions.jsonl")
MAP_PATH = Path("evaluation/evidence_chunk_map.json")


def load_questions() -> list[dict]:
    questions = []

    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            questions.append(json.loads(line))

    return questions


def load_mapping() -> dict:
    if not MAP_PATH.exists():
        return {}

    with MAP_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    questions = load_questions()
    mapping = load_mapping()

    answerable = [
        q for q in questions
        if q["answerable"]
    ]

    unanswerable = [
        q for q in questions
        if not q["answerable"]
    ]

    mapped_ids = set(mapping.keys())

    mapped_answerable = [
        q["question_id"]
        for q in answerable
        if q["question_id"] in mapped_ids
    ]

    unmapped_answerable = [
        q["question_id"]
        for q in answerable
        if q["question_id"] not in mapped_ids
    ]

    print("\nBenchmark summary")
    print("=" * 50)
    print(f"Total questions: {len(questions)}")
    print(f"Answerable: {len(answerable)}")
    print(f"Unanswerable: {len(unanswerable)}")

    print("\nMapping progress")
    print("=" * 50)
    print(f"Mapped answerable questions: {len(mapped_answerable)}")
    print(f"Remaining answerable questions: {len(unmapped_answerable)}")

    print("\nMapped:")
    print(", ".join(mapped_answerable) or "None")

    print("\nRemaining:")
    print(", ".join(unmapped_answerable) or "None")


if __name__ == "__main__":
    main()