import argparse
import re
from pathlib import Path


MARKDOWN_DIR = Path("data/markdown")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_evidence(file_path: Path, keywords: list[str], context_lines: int = 8):
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    matches = []

    for index, line in enumerate(lines):
        normalized_line = normalize(line).lower()

        if any(keyword.lower() in normalized_line for keyword in keywords):
            start = max(0, index - context_lines)
            end = min(len(lines), index + context_lines + 1)

            passage = "\n".join(lines[start:end])

            matches.append(
                {
                    "line_number": index + 1,
                    "passage": passage,
                }
            )

    return matches


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "file",
        help="Markdown filename inside data/markdown",
    )

    parser.add_argument(
        "keywords",
        nargs="+",
        help="Keywords or phrases to search for",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of matches to display",
    )

    args = parser.parse_args()

    file_path = MARKDOWN_DIR / args.file

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    matches = find_evidence(file_path, args.keywords)

    if not matches:
        print("No matches found.")
        return

    print(f"\nFound {len(matches)} candidate passages.\n")

    for number, match in enumerate(matches[: args.limit], start=1):
        print("=" * 80)
        print(
            f"Candidate {number} | "
            f"around line {match['line_number']}"
        )
        print("=" * 80)
        print(match["passage"])
        print()


if __name__ == "__main__":
    main()