# Hybrid Retrieval Experiment

## Objective
Determine whether Azure AI Search hybrid retrieval improves upon the
BM25 and dense retrieval baselines.

## Experimental Controls
- Same 44 answerable benchmark questions
- Same indexed corpus
- Same frozen evidence-to-chunk mapping
- Same recursive markdown-aware chunking
- Same Top-K = 10
- Global retrieval without ground-truth metadata filters

## Results
[BM25 vs Dense vs Hybrid table]

## Findings and Decision
[overall + category observations and decision to retain Dense]