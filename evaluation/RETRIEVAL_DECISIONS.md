# Retrieval Architecture Decisions

## Final Production Retrieval Strategy

The final RAG retrieval path uses:

1. Deterministic query routing
2. Query-aware company/year detection
3. Dense retrieval
4. Balanced evidence selection
5. Top-5 provenance-rich context
6. LLM answer generation with citations and abstention

Exact supported KPI questions are routed to PostgreSQL rather than the vector RAG path.

---

## Retrieval Experiments

### BM25
Rejected.

Dense retrieval substantially outperformed BM25 on the frozen retrieval benchmark.

### Hybrid Retrieval
Tested but not selected.

Hybrid improved some top-1 results but did not outperform Dense retrieval on the metrics most relevant to the application, including Recall@5, Complete Evidence Success@5, MRR, and latency.

### Chunking
Markdown-aware recursive chunking was retained.

Alternative structural chunking did not improve retrieval quality.

### Context Size
Top-5 and top-10 generation contexts were compared.

Top-10 roughly doubled prompt context while producing inconsistent answer-quality improvements and additional irrelevant evidence.

Top-5 was retained.

### Query-Aware Retrieval
Selected.

Company/year-aware retrieval improved evidence coverage, particularly for multi-company questions, while explicit source provenance reduced incorrect company attribution.

### Reranking
Rejected.

Two reranking approaches were tested:

- MiniLM cross-encoder
- BAAI/bge-reranker-base

Dense top-20 retrieval showed that missing evidence was often present deeper in the candidate set.

BGE improved ranking for some individual questions, but the final end-to-end experiment on four targeted weak cases produced:

- 0 improved
- 4 unchanged
- 0 regressed

Final correctness total remained unchanged.

Reranking also introduced additional latency and complexity.

Therefore, reranking was not included in the final production architecture.

---

## Remaining Limitation

The primary remaining RAG weakness is multi-evidence coverage.

Broad qualitative questions may require several complementary pieces of evidence distributed across multiple chunks. Ranking a single chunk more accurately did not consistently improve final answer completeness.

Future work could investigate query decomposition or multi-query retrieval, but these were intentionally not added to avoid unnecessary complexity and benchmark overfitting.