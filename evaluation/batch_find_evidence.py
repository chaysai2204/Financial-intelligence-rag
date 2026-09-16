import json
import re
from pathlib import Path

CANDIDATE_PATH = Path("evaluation/candidate_questions.jsonl")
MARKDOWN_DIR = Path("data/markdown")
OUTPUT_PATH = Path("evaluation/evidence_candidates.txt")

# document_id -> local Markdown filename
DOCUMENT_FILES = {
    "AAPL_2023_10K": "AAPL_2023_10-K.md",
    "AAPL_2024_10K": "AAPL_2024_10-K.md",
    "MSFT_2023_10K": "MSFT_2023_10-K.md",
    "MSFT_2024_10K": "MSFT_2024_10-K.md",
    "NVDA_2023_10K": "NVDA_2023_10-K.md",
}

# These terms are ONLY for locating ground-truth candidates.
# They are NOT used by the retrieval systems we will evaluate.
SEARCH_TERMS = {
    "Q006": ["Services", "net sales"],
    "Q007": ["total net sales", "383,285"],
    "Q008": ["total revenue", "revenue"],
    "Q009": ["total revenue", "revenue"],
    "Q010": ["revenue"],
    "Q011": ["net income"],
    "Q012": ["net income"],
    "Q013": ["Data Center", "revenue"],
    "Q014": ["iPhone", "net sales"],

    "Q015": ["net income"],
    "Q016": ["revenue"],
    "Q017": ["revenue"],
    "Q018": ["Services", "net sales"],
    "Q019": ["net income"],
    "Q020": ["iPhone", "net sales"],

    "Q021": ["supply chain", "suppliers", "manufacturing"],
    "Q022": ["competition", "competitive"],
    "Q023": ["forecast", "demand"],
    "Q024": ["third-party", "suppliers", "manufacturing"],
    "Q025": ["cybersecurity", "security", "cyber"],
    "Q026": ["third-party", "manufacturing", "foundry"],

    "Q027": ["Services", "net sales"],
    "Q028": ["net income"],
    "Q029": ["revenue"],
    "Q030": ["net income"],
    "Q031": ["iPhone", "net sales"],
    "Q032": ["Services", "total net sales"],

    "Q033": ["total net sales", "revenue"],
    "Q034": ["net income"],
    "Q035": ["supply", "suppliers", "manufacturing"],
    "Q036": ["competition", "competitive"],
    "Q037": ["total net sales", "revenue"],
    "Q038": ["third-party", "manufacturing", "suppliers"],
    "Q039": ["net income"],

    "Q040": ["Services", "net sales"],
    "Q041": ["cloud", "Azure"],
    "Q042": ["third-party", "manufacturing", "foundry"],
    "Q043": ["international", "net sales"],
    "Q044": ["forecast", "demand", "revenue"],
    "Q045": ["cloud", "Azure", "services"],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_passages(
    file_path: Path,
    keywords: list[str],
    context_lines: int = 6,
    limit: int = 5,
):
    lines = file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    scored_matches = []

    for index, line in enumerate(lines):
        normalized_line = normalize(line).lower()

        matched_terms = [
            keyword
            for keyword in keywords
            if keyword.lower() in normalized_line
        ]

        if not matched_terms:
            continue

        start = max(0, index - context_lines)
        end = min(len(lines), index + context_lines + 1)

        passage = "\n".join(lines[start:end])

        scored_matches.append(
            {
                "line_number": index + 1,
                "passage": passage,
                "score": len(matched_terms),
            }
        )

    # Prefer lines matching more of our annotation terms.
    scored_matches.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_matches[:limit]


def main():
    questions = []

    with CANDIDATE_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                questions.append(json.loads(line))

    answerable_questions = [
        question
        for question in questions
        if question["answerable"]
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8") as output:
        for question in answerable_questions:
            question_id = question["question_id"]
            search_terms = SEARCH_TERMS.get(question_id, [])

            output.write("=" * 100 + "\n")
            output.write(f"{question_id}: {question['question']}\n")
            output.write(f"Category: {question['category']}\n")
            output.write(
                f"Search terms: {', '.join(search_terms)}\n"
            )
            output.write("=" * 100 + "\n\n")

            if not search_terms:
                output.write("NO SEARCH TERMS CONFIGURED\n\n")
                continue

            for document_id in question["expected_document_ids"]:
                filename = DOCUMENT_FILES.get(document_id)

                output.write(f"DOCUMENT: {document_id}\n")

                if filename is None:
                    output.write(
                        "No Markdown mapping configured.\n\n"
                    )
                    continue

                file_path = MARKDOWN_DIR / filename

                if not file_path.exists():
                    output.write(
                        f"Markdown file not found: {file_path}\n\n"
                    )
                    continue

                matches = find_passages(
                    file_path=file_path,
                    keywords=search_terms,
                )

                if not matches:
                    output.write(
                        "No candidate passages found.\n\n"
                    )
                    continue

                for number, match in enumerate(matches, start=1):
                    output.write(
                        f"\n--- Candidate {number} "
                        f"(around line {match['line_number']}) ---\n"
                    )
                    output.write(match["passage"])
                    output.write("\n")

                output.write("\n")

            output.write("\n")

    print(
        f"Processed {len(answerable_questions)} "
        "answerable questions."
    )
    print(f"Saved review file to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()