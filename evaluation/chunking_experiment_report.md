# Chunking Experiment Report

## Objective

The goal of this experiment was to determine whether a document-structure-aware chunking strategy could improve retrieval quality over the existing recursive character chunking baseline.

The existing baseline uses `RecursiveCharacterTextSplitter` with:

* Maximum chunk size: 1500 characters
* Chunk overlap: 200 characters
* Markdown-aware separator priority

The experimental strategy, Structural v2, first splits financial reports using Markdown H1/H2 headings, merges neighboring small sections, and recursively splits oversized sections.

## Semantic Chunking Investigation

Embedding-based semantic chunking was initially prototyped using LangChain's `SemanticChunker`.

However, even the smallest benchmark filing produced more than one thousand sentence groups and triggered Azure OpenAI embedding rate limits during semantic boundary generation.

Because semantic chunking introduced an additional embedding-intensive preprocessing stage before the final chunk embeddings were generated, it was not selected for the corpus-wide experiment.

## Structural Chunking Development

The first structural implementation treated every Markdown heading as a hard boundary.

Across the five benchmark filings:

| Metric                          | Recursive | Structural v1 |
| ------------------------------- | --------: | ------------: |
| Total chunks                    |      2316 |          2952 |
| Average characters              |     964.7 |         754.3 |
| Median characters               |    1083.0 |         784.0 |
| Chunks below 250 characters     |       234 |           699 |
| Percentage below 250 characters |    10.10% |        23.68% |

Structural v1 introduced excessive fragmentation and was therefore rejected.

Structural v2 added small-section merging while preserving Markdown headings.

| Metric                          | Recursive | Structural v2 |
| ------------------------------- | --------: | ------------: |
| Total chunks                    |      2316 |          2393 |
| Average characters              |     964.7 |         931.0 |
| Median characters               |    1083.0 |        1018.0 |
| Chunks below 250 characters     |       234 |           256 |
| Percentage below 250 characters |    10.10% |        10.70% |

This produced a distribution sufficiently close to the recursive baseline for a controlled comparison.

Manual inspection also confirmed that Structural v2 preserved important financial tables, headings, risk-factor sections, years, units, and surrounding context.

## Experimental Scope

The full recursive benchmark index already occupied approximately 48.75 MB in Azure AI Search. Because the available Azure Search capacity was limited, duplicating the complete five-document corpus for another chunking strategy was avoided.

Instead, a controlled subset experiment was performed using:

* Document: `AAPL_2024_10K`
* Recursive chunks: 427
* Structural v2 chunks: 444
* Benchmark questions: 13
* Retrieval strategy: Dense vector retrieval
* Top K: 10
* Same embedding model
* Same Azure AI Search schema
* Same benchmark questions
* Independently verified evidence-to-chunk mappings for each chunking strategy

Only the chunking strategy was intentionally changed.

## Results

| Metric               | Recursive | Structural v2 |
| -------------------- | --------: | ------------: |
| Recall@1             |    0.3462 |        0.2692 |
| Recall@5             |    0.6923 |        0.6538 |
| Recall@10            |    0.9231 |        0.9231 |
| Complete Evidence@1  |    0.3077 |        0.2308 |
| Complete Evidence@5  |    0.6923 |        0.6154 |
| Complete Evidence@10 |    0.9231 |        0.9231 |
| MRR                  |    0.5417 |        0.4896 |
| Mean latency         |  543.9 ms |      274.7 ms |
| Median latency       |  218.0 ms |      247.0 ms |

Structural v2 matched the recursive baseline at Recall@10 and Complete Evidence@10, but performed worse on top-ranked retrieval quality.

Recursive chunking achieved higher:

* Recall@1
* Recall@5
* Complete Evidence@1
* Complete Evidence@5
* MRR

Structural v2 improved some individual retrieval cases but did not provide a consistent aggregate improvement.

Latency was not used as the primary decision criterion because the recursive mean latency was substantially higher than its median, suggesting that a small number of slower requests affected the mean. Structural v2 also had a slightly higher median latency.

## Decision

Structural v2 was **not promoted to the default chunking strategy**.

The existing recursive markdown-aware chunking strategy remains the project baseline because it produced stronger top-ranked retrieval quality while requiring no additional document-structure-specific logic.

The experiment also demonstrated that cleaner-looking document boundaries do not necessarily translate into better retrieval performance.

## Engineering Takeaway

Chunking changes were evaluated empirically rather than adopted based on intuition.

The experiment followed the sequence:

1. Measure the existing recursive baseline.
2. Prototype semantic chunking.
3. Reject semantic chunking when preprocessing cost and API rate limits became problematic.
4. Prototype structure-aware chunking.
5. Reject Structural v1 due to excessive fragmentation.
6. Improve the design with section merging.
7. Validate Structural v2 chunk statistics and content manually.
8. Build an isolated experimental index.
9. Create independently verified retrieval ground truth.
10. Compare both strategies using the same Dense retrieval setup.

The final decision was to retain recursive chunking because Structural v2 did not demonstrate sufficient retrieval improvement.
