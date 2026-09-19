import json
import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv(dotenv_path=".env")


BENCHMARK_FILE = "evaluation/retrieval_questions.jsonl"
OUTPUT_FILE = "evaluation/structural_mapping_candidates.json"

INDEX_NAME = "financial-documents-structural-v2"
TARGET_DOC = "AAPL_2024_10K"

TOP_K = 10


def load_questions():
    questions = []

    with open(
        BENCHMARK_FILE,
        encoding="utf-8",
    ) as file:

        for line in file:
            q = json.loads(line)

            if not q.get(
                "answerable",
                False,
            ):
                continue

            expected_docs = set(
                q.get(
                    "expected_document_ids",
                    [],
                )
            )

            if expected_docs == {
                TARGET_DOC
            }:
                questions.append(q)

    return questions


def main():

    client = SearchClient(
        endpoint=os.getenv(
            "AZURE_SEARCH_ENDPOINT"
        ),
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(
            os.getenv(
                "AZURE_SEARCH_API_KEY"
            )
        ),
    )

    questions = load_questions()

    print(
        f"Questions selected: "
        f"{len(questions)}"
    )

    output = []

    for q in questions:

        print(
            f"\nProcessing "
            f"{q['question_id']}"
        )

        question_entry = {
            "question_id":
                q["question_id"],
            "question":
                q["question"],
            "category":
                q["category"],
            "evidence_items": [],
        }

        for evidence_index, evidence in enumerate(
            q.get("evidence", [])
        ):

            evidence_text = evidence[
                "evidence_text"
            ]

            results = client.search(
                search_text=evidence_text,
                filter=(
                    "document_id eq "
                    f"'{TARGET_DOC}'"
                ),
                top=TOP_K,
                select=[
                    "id",
                    "document_id",
                    "chunk_index",
                    "content",
                ],
            )

            candidates = []

            for rank, result in enumerate(
                results,
                start=1,
            ):
                candidates.append(
                    {
                        "rank": rank,
                        "chunk_id":
                            result.get("id"),
                        "chunk_index":
                            result.get(
                                "chunk_index"
                            ),
                        "content":
                            result.get(
                                "content"
                            ),
                    }
                )

            question_entry[
                "evidence_items"
            ].append(
                {
                    "evidence_index":
                        evidence_index,
                    "evidence_text":
                        evidence_text,
                    "section_hint":
                        evidence.get(
                            "section_hint"
                        ),
                    "candidates":
                        candidates,
                }
            )

        output.append(
            question_entry
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print(
        f"\nWrote candidates to "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()