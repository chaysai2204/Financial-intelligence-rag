from pathlib import Path
from statistics import mean, median

from ingestion.semantic_chunker import chunk_markdown
from ingestion.structural_chunker import chunk_markdown_structural


FILES = [
    "AAPL_2023_10-K.md",
    "AAPL_2024_10-K.md",
    "MSFT_2023_10-K.md",
    "MSFT_2024_10-K.md",
    "NVDA_2023_10-K.md",
]

BASE_DIR = Path("data/markdown")


def calculate_stats(chunks):
    sizes = [
        len(chunk.page_content)
        for chunk in chunks
    ]

    return {
        "chunks": len(chunks),
        "average": mean(sizes),
        "median": median(sizes),
        "minimum": min(sizes),
        "maximum": max(sizes),
        "small": sum(
            size < 250
            for size in sizes
        ),
    }


def print_stats(name, stats):
    print(f"{name}")
    print(f"  Chunks:      {stats['chunks']}")
    print(f"  Avg chars:   {stats['average']:.1f}")
    print(f"  Median:      {stats['median']:.1f}")
    print(f"  Min:         {stats['minimum']}")
    print(f"  Max:         {stats['maximum']}")
    print(f"  <250 chars:  {stats['small']}")


recursive_all = []
structural_all = []


for filename in FILES:
    path = BASE_DIR / filename

    recursive_chunks = chunk_markdown(
        markdown_file=str(path)
    )

    structural_chunks = chunk_markdown_structural(
        markdown_file=str(path)
    )

    recursive_all.extend(recursive_chunks)
    structural_all.extend(structural_chunks)

    recursive_stats = calculate_stats(
        recursive_chunks
    )

    structural_stats = calculate_stats(
        structural_chunks
    )

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    print_stats(
        "RECURSIVE",
        recursive_stats
    )

    print()

    print_stats(
        "STRUCTURAL",
        structural_stats
    )


print("\n" + "=" * 70)
print("CORPUS TOTAL")
print("=" * 70)

recursive_total = calculate_stats(
    recursive_all
)

structural_total = calculate_stats(
    structural_all
)

print_stats(
    "RECURSIVE",
    recursive_total
)

print()

print_stats(
    "STRUCTURAL",
    structural_total
)

recursive_small_pct = (
    recursive_total["small"]
    / recursive_total["chunks"]
    * 100
)

structural_small_pct = (
    structural_total["small"]
    / structural_total["chunks"]
    * 100
)

print()
print(
    f"Recursive <250 percentage: "
    f"{recursive_small_pct:.2f}%"
)

print(
    f"Structural <250 percentage: "
    f"{structural_small_pct:.2f}%"
)