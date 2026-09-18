# Retrieval Baseline Evaluation

## Objective

Establish reproducible retrieval baselines before introducing hybrid retrieval,
reranking, or alternative chunking strategies.

The experiment compares lexical BM25 retrieval against dense vector retrieval
on the same indexed financial-report corpus and benchmark.

## Corpus and Chunking

Financial reports are converted from PDF to Markdown using PyMuPDF4LLM.

The current indexed corpus uses a markdown-aware
`RecursiveCharacterTextSplitter` with:

- Chunk size: 1500 characters
- Chunk overlap: 200 characters
- Preferred boundaries: Markdown headings, paragraphs, lines, sentences,
  words, and finally characters

This is the baseline chunking strategy. Semantic chunking is not used in this
experiment.

## Evaluation Dataset

The retrieval benchmark contains 50 questions.

- 44 answerable questions are used for retrieval evaluation.
- 6 unanswerable questions are excluded from retrieval Recall/MRR metrics.
- Unanswerable questions will later be used to evaluate abstention behavior.

The benchmark contains factual, paraphrase, qualitative, temporal,
cross-company, and evidence-seeking questions.

Ground-truth evidence-to-chunk mappings were generated using deterministic
candidate generation and manually verified before evaluation.

## Evaluation Protocol

Both BM25 and dense retrieval receive:

- The same raw user question
- The same indexed corpus
- No ground-truth company/year filters
- Top-K = 10

Expected benchmark metadata is not supplied to the retriever because doing so
would leak ground-truth information.

Dense retrieval includes query-embedding generation as part of the retrieval
pipeline.

### Metrics

- Recall@1
- Recall@5
- Recall@10
- Mean Reciprocal Rank (MRR)
- Complete Evidence Success@1
- Complete Evidence Success@5
- Complete Evidence Success@10
- Mean retrieval latency
- Median retrieval latency
- P95 retrieval latency

Recall measures evidence coverage. Complete Evidence Success requires all
required evidence for a question to be retrieved.

## Results

| Metric | BM25 | Dense |
|---|---:|---:|
| Recall@5 | 0.3030 | 0.4886 |
| Recall@10 | 0.3485 | 0.5795 |
| MRR | 0.2137 | 0.4304 |
| Median Latency | 65.5 ms | 208.9 ms |

Full metrics, including Recall@1, Complete Evidence Success, latency
statistics, category-level results, and per-question outputs, are stored in:

- `evaluation/retrieval_summary.json`
- `evaluation/retrieval_results.json`

## Interpretation

Dense retrieval substantially outperformed BM25 on the current benchmark.

Recall@10 increased from 0.3485 with BM25 to 0.5795 with dense retrieval.
MRR increased from 0.2137 to 0.4304, indicating that dense retrieval also
tended to rank relevant evidence earlier.

However, this improvement came with higher latency. Median retrieval latency
increased from approximately 65.5 ms for BM25 to 208.9 ms for dense retrieval.

The per-question results also show complementary behavior. BM25 performs well
for some questions containing strong lexical or numeric signals, while dense
retrieval performs better for many semantic and paraphrased queries.

Neither strategy achieves complete evidence retrieval consistently across the
benchmark.

## Engineering Decision

The baseline results justify testing hybrid retrieval.

Hybrid retrieval will combine lexical and dense signals and will be evaluated
against these frozen baselines using the same benchmark and ground-truth
evidence mappings.

Hybrid retrieval will only be retained if the experiment demonstrates a useful
improvement relative to the additional complexity and latency.

No reranking or chunking changes will be introduced during the hybrid
experiment so that retrieval strategy remains the isolated experimental
variable.

## Baseline Status

This experiment establishes the Phase 5 retrieval baseline:

**Recursive chunking + BM25 vs. Recursive chunking + Dense retrieval**

These results should remain frozen as the comparison point for subsequent
retrieval experiments.