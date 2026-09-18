import json
import os
import sys

from dotenv import load_dotenv

from vectorstore.azure_ai_search import AzureAISearchVectorStore


BENCHMARK_PATH = "evaluation/retrieval_questions.jsonl"
MAPPING_PATH = "evaluation/evidence_chunk_map.json"


def load_benchmark(path: str) -> dict:
    questions = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            item = json.loads(line)
            questions[item["question_id"]] = item

    return questions


def load_mapping(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    load_dotenv(".env")

    benchmark = load_benchmark(BENCHMARK_PATH)
    mapping = load_mapping(MAPPING_PATH)

    store = AzureAISearchVectorStore(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    )

    errors = []
    checked_chunks = set()

    answerable_questions = {
        qid: question
        for qid, question in benchmark.items()
        if question.get("answerable") is True
    }

    print("=" * 80)
    print("EVIDENCE CHUNK MAP VALIDATION")
    print("=" * 80)

    print(f"Benchmark questions: {len(benchmark)}")
    print(f"Answerable questions: {len(answerable_questions)}")
    print(f"Mapped questions: {len(mapping)}")
    print()

    # ---------------------------------------------------------
    # 1. Check every answerable question exists in mapping
    # ---------------------------------------------------------
    for question_id in answerable_questions:
        if question_id not in mapping:
            errors.append(
                f"{question_id}: answerable benchmark question missing from mapping"
            )

    # ---------------------------------------------------------
    # 2. Check mapping contains no unexpected questions
    # ---------------------------------------------------------
    for question_id in mapping:
        if question_id not in benchmark:
            errors.append(
                f"{question_id}: exists in mapping but not benchmark"
            )
            continue

        if benchmark[question_id].get("answerable") is not True:
            errors.append(
                f"{question_id}: unanswerable question should not have evidence mapping"
            )

    # ---------------------------------------------------------
    # 3. Validate every mapped evidence item
    # ---------------------------------------------------------
    for question_id, mapping_entry in mapping.items():

        if question_id not in benchmark:
            continue

        benchmark_question = benchmark[question_id]

        expected_evidence = benchmark_question.get("evidence", [])
        mapped_evidence = mapping_entry.get("evidence_items", [])

        expected_indices = set(range(1, len(expected_evidence) + 1))

        mapped_indices = {
            item.get("evidence_index")
            for item in mapped_evidence
        }

        if mapped_indices != expected_indices:
            errors.append(
                f"{question_id}: evidence indexes mismatch. "
                f"Expected {sorted(expected_indices)}, "
                f"got {sorted(mapped_indices)}"
            )

        for mapped_item in mapped_evidence:

            evidence_index = mapped_item.get("evidence_index")

            if not isinstance(evidence_index, int):
                errors.append(
                    f"{question_id}: invalid evidence_index {evidence_index}"
                )
                continue

            if evidence_index < 1 or evidence_index > len(expected_evidence):
                errors.append(
                    f"{question_id}: evidence_index {evidence_index} out of range"
                )
                continue

            benchmark_evidence = expected_evidence[evidence_index - 1]

            expected_document_id = benchmark_evidence["document_id"]

            groups = mapped_item.get("acceptable_chunk_groups")

            if not isinstance(groups, list) or not groups:
                errors.append(
                    f"{question_id} evidence {evidence_index}: "
                    f"acceptable_chunk_groups is missing or empty"
                )
                continue

            for group_number, group in enumerate(groups, start=1):

                if not isinstance(group, list) or not group:
                    errors.append(
                        f"{question_id} evidence {evidence_index} "
                        f"group {group_number}: group is empty or invalid"
                    )
                    continue

                for chunk_id in group:

                    if not isinstance(chunk_id, str) or not chunk_id.strip():
                        errors.append(
                            f"{question_id} evidence {evidence_index} "
                            f"group {group_number}: invalid chunk ID"
                        )
                        continue

                    cache_key = (chunk_id, expected_document_id)

                    if cache_key in checked_chunks:
                        continue

                    checked_chunks.add(cache_key)

                    try:
                        document = store.client.get_document(
                            key=chunk_id
                        )

                    except Exception as exc:
                        errors.append(
                            f"{question_id} evidence {evidence_index}: "
                            f"chunk {chunk_id} not found in Azure Search "
                            f"({exc})"
                        )
                        continue

                    actual_document_id = document.get("document_id")

                    if actual_document_id != expected_document_id:
                        errors.append(
                            f"{question_id} evidence {evidence_index}: "
                            f"chunk {chunk_id} belongs to "
                            f"{actual_document_id}, expected "
                            f"{expected_document_id}"
                        )

    print(f"Unique chunk/document pairs checked: {len(checked_chunks)}")
    print()

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    if errors:
        print("VALIDATION FAILED")
        print("=" * 80)

        for error in errors:
            print(f"- {error}")

        print()
        print(f"Total errors: {len(errors)}")
        sys.exit(1)

    print("VALIDATION PASSED")
    print("=" * 80)
    print("All answerable benchmark questions are mapped.")
    print("All evidence items have valid acceptable chunk groups.")
    print("All mapped chunks exist in Azure AI Search.")
    print("All mapped chunks belong to the expected documents.")


if __name__ == "__main__":
    main()