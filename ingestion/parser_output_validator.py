import re
from pathlib import Path


COMMON_WORDS = {
    "the",
    "of",
    "and",
    "to",
    "in",
    "for",
    "a",
    "is",
    "on",
    "that",
    "as",
    "by",
    "with",
    "from",
    "our",
    "we",
}


def validate_markdown_output(
    markdown_path: str | Path
) -> None:
    """
    Validate that PDF-to-Markdown parsing produced
    usable text before chunking and embedding.
    """

    markdown_path = Path(markdown_path)

    if not markdown_path.exists():
        raise ValueError(
            f"Markdown output was not created: {markdown_path}"
        )

    text = markdown_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    if len(text.strip()) < 100:
        raise ValueError(
            f"Markdown output is too short or empty: "
            f"{markdown_path.name}"
        )

    words = re.findall(
        r"[A-Za-z]+",
        text.lower()
    )

    if len(words) < 20:
        raise ValueError(
            f"Markdown output does not contain enough "
            f"readable text: {markdown_path.name}"
        )

    common_word_count = sum(
        word in COMMON_WORDS
        for word in words
    )

    common_word_ratio = (
        common_word_count / len(words)
    )

    if common_word_ratio < 0.03:
        raise ValueError(
            f"Markdown output appears unreadable or corrupted: "
            f"{markdown_path.name}"
        )