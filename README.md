# AI-Powered Investor Intelligence Platform

An AI-powered financial document intelligence platform for analyzing company annual reports using Retrieval-Augmented Generation (RAG).

The application allows users to upload financial reports, extract key financial metrics, store structured results, and ask natural-language questions about the uploaded documents.

## Current Features

* PDF annual report ingestion
* PDF-to-Markdown conversion
* Semantic document chunking
* Azure OpenAI embeddings
* Azure AI Search indexing and retrieval
* Retrieval-Augmented Generation (RAG)
* Structured financial KPI extraction
* PostgreSQL storage
* FastAPI backend
* Interactive financial dashboard
* AI-powered document Q&A

## Architecture

The current pipeline follows:

```text
PDF Report
    ↓
PDF to Markdown
    ↓
Semantic Chunking
    ↓
Azure OpenAI Embeddings
    ↓
Azure AI Search
    ↓
RAG Retrieval
    ↓
Azure OpenAI
    ↓
Financial Q&A / KPI Extraction
    ↓
PostgreSQL + Dashboard
```

Architecture diagrams are available under:

```text
docs/architecture/
```

## Technology Stack

* Python
* FastAPI
* Azure OpenAI
* Azure AI Search
* LangChain
* PyMuPDF4LLM
* PostgreSQL
* Jinja2
* HTML / CSS / JavaScript

## Project Status

The baseline end-to-end application is functional locally.

Planned engineering improvements include:

* richer chunk metadata
* dense vector retrieval
* hybrid lexical + vector retrieval
* reranking
* source citations
* RAG evaluation
* retrieval benchmarking
* automated testing
* Docker containerization
* Azure Kubernetes Service deployment
* CI/CD

## Sample Data

The project currently uses annual reports from:

* Apple
* Microsoft
* Tesla

## Development

The project is currently under active development as the RAG retrieval, evaluation, and deployment architecture are improved.
