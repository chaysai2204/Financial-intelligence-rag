import os
import time
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.query_metrics import get_metric
from llm.azure_openai import (
    get_embedding_client,
    get_openai_client,
)
from rag.query_aware_retriever import (
    build_retrieval_targets,
    query_aware_retrieve,
)
from rag.query_router import route_query
from utils.observability import get_logger, log_event
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)


router = APIRouter()
logger = get_logger()


class ChatRequest(BaseModel):
    question: str
    company: str | None = None
    year: int | None = None


METRIC_DISPLAY_NAMES = {
    "revenue": "Revenue",
    "net_income": "Net income",
    "operating_income": "Operating income",
    "operating_cash_flow": "Cash flow from operating activities",
    "total_assets": "Total assets",
    "total_liabilities": "Total liabilities",
}


def format_structured_answer(
    *,
    company: str,
    year: int,
    metric: str,
    value,
) -> str:
    """
    Format structured PostgreSQL KPI values.

    Database values are stored in USD millions.
    """

    display_name = METRIC_DISPLAY_NAMES[metric]
    formatted_value = f"{value:,.0f}"

    return (
        f"{display_name} for {company} in fiscal year {year} "
        f"was ${formatted_value} million."
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    total_start = time.perf_counter()

    try:
        # -----------------------------------------------------
        # 1. Route the question
        # -----------------------------------------------------

        decision = route_query(
            question=request.question,
            company=request.company,
            year=request.year,
        )

        log_event(
            logger,
            "route_selected",
            request_id=request_id,
            route=decision.route,
            metric=decision.metric,
            reason=decision.reason,
            company=request.company,
            year=request.year,
        )

        # -----------------------------------------------------
        # 2. Structured PostgreSQL path
        # -----------------------------------------------------

        if decision.route == "structured":
            db_start = time.perf_counter()

            result = get_metric(
                company=request.company,
                fiscal_year=request.year,
                metric=decision.metric,
            )

            db_ms = (
                time.perf_counter() - db_start
            ) * 1000

            db_hit = (
                result is not None
                and result["value"] is not None
            )

            log_event(
                logger,
                "structured_lookup",
                request_id=request_id,
                company=request.company,
                year=request.year,
                metric=decision.metric,
                db_hit=db_hit,
                db_ms=round(db_ms, 2),
            )

            # Structured database may not contain this filing yet.
            # Fall back to RAG instead of returning an incorrect answer.
            if db_hit:
                answer = format_structured_answer(
                    company=result["company"],
                    year=result["fiscal_year"],
                    metric=decision.metric,
                    value=result["value"],
                )

                source = {
                    "citation_id": 1,
                    "document_id": result["document_id"],
                    "company": result["company"],
                    "ticker": result["ticker"],
                    "year": result["fiscal_year"],
                    "filing_type": result["filing_type"],
                    "source_file": None,
                    "chunk_index": None,
                    "rank": None,
                    "evidence": (
                        f"{METRIC_DISPLAY_NAMES[decision.metric]}: "
                        f"{result['value']} million"
                    ),
                }

                total_ms = (
                    time.perf_counter() - total_start
                ) * 1000

                log_event(
                    logger,
                    "request_completed",
                    request_id=request_id,
                    route="structured",
                    company=result["company"],
                    year=result["fiscal_year"],
                    metric=decision.metric,
                    db_hit=True,
                    source_count=1,
                    total_ms=round(total_ms, 2),
                    status="success",
                )

                return {
                    "answer": answer,
                    "sources": [source],
                    "route": "structured",
                }

            log_event(
                logger,
                "structured_fallback",
                request_id=request_id,
                original_route="structured",
                fallback_route="rag",
                company=request.company,
                year=request.year,
                metric=decision.metric,
            )

        # -----------------------------------------------------
        # 3. Query-aware Dense RAG path
        # -----------------------------------------------------

        vector_store = AzureAISearchVectorStore(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        )

        embeddings = get_embedding_client()

        retriever = DenseRetriever(
            vector_store.client,
            embeddings,
        )

        # Detect company/year targets used by query-aware retrieval.
        retrieval_targets = build_retrieval_targets(
            request.question
        )

        log_event(
            logger,
            "retrieval_targets",
            request_id=request_id,
            targets=[
                {
                    "company": target.company,
                    "year": target.year,
                }
                for target in retrieval_targets
            ],
        )

        # -----------------------------------------------------
        # 4. Retrieval timing
        # -----------------------------------------------------

        retrieval_start = time.perf_counter()

        docs = query_aware_retrieve(
            retriever=retriever,
            question=request.question,
            final_top_k=5,
            per_target_k=5,
        )

        retrieval_ms = (
            time.perf_counter() - retrieval_start
        ) * 1000

        # -----------------------------------------------------
        # 5. Build provenance-rich context
        # -----------------------------------------------------

        context_blocks = []
        sources = []

        for citation_id, doc in enumerate(
            docs,
            start=1,
        ):
            metadata = doc.metadata

            context_blocks.append(
                f"[Source {citation_id}]\n"
                f"Company: {metadata.get('company')}\n"
                f"Ticker: {metadata.get('ticker')}\n"
                f"Fiscal Year: {metadata.get('year')}\n"
                f"Document ID: {metadata.get('document_id')}\n\n"
                f"Evidence:\n"
                f"{doc.page_content}"
            )

            sources.append(
                {
                    "citation_id": citation_id,
                    "document_id": metadata.get(
                        "document_id"
                    ),
                    "company": metadata.get("company"),
                    "ticker": metadata.get("ticker"),
                    "year": metadata.get("year"),
                    "filing_type": metadata.get(
                        "filing_type"
                    ),
                    "source_file": metadata.get(
                        "source_file"
                    ),
                    "chunk_index": metadata.get(
                        "chunk_index"
                    ),
                    "rank": metadata.get("rank"),
                    "evidence": doc.page_content,
                }
            )

        retrieved_document_ids = sorted(
            {
                source["document_id"]
                for source in sources
                if source["document_id"]
            }
        )

        retrieved_companies = sorted(
            {
                source["company"]
                for source in sources
                if source["company"]
            }
        )

        retrieved_years = sorted(
            {
                source["year"]
                for source in sources
                if source["year"] is not None
            }
        )

        log_event(
            logger,
            "retrieval_completed",
            request_id=request_id,
            retrieval_ms=round(retrieval_ms, 2),
            source_count=len(sources),
            document_ids=retrieved_document_ids,
            companies=retrieved_companies,
            years=retrieved_years,
        )

        context = "\n\n".join(context_blocks)

        # -----------------------------------------------------
        # 6. Evidence-grounded generation
        # -----------------------------------------------------

        prompt = f"""
You are an expert financial analyst.

Answer the user's question using only the provided sources.

Citation rules:
- Cite the supporting source using [Source N].
- Every factual claim must be supported by at least one source.
- Use only source numbers that appear in the provided context.
- Do not invent citations.
- If the provided sources do not contain enough evidence to answer the question, say that you do not have enough information.
- When abstaining, do not cite unrelated sources as if they support the missing answer.
- Never substitute data from a different fiscal year for the year requested.
- Preserve company and fiscal-year attribution exactly as shown in each source.
- Never attribute one company's evidence to another company.
- For comparison questions, answer each company separately before comparing them.
- Do not claim that a filing is unavailable if the provided sources contain evidence from that filing.

Context:
{context}

User Question:
{request.question}

Answer:
"""

        client = get_openai_client()

        # -----------------------------------------------------
        # 7. LLM timing
        # -----------------------------------------------------

        llm_start = time.perf_counter()

        response = client.chat.completions.create(
            model=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT"
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        llm_ms = (
            time.perf_counter() - llm_start
        ) * 1000

        answer = response.choices[0].message.content

        # -----------------------------------------------------
        # 8. Abstention detection
        # -----------------------------------------------------

        answer_lower = answer.lower()

        abstained = (
            len(sources) == 0
            or any(
                phrase in answer_lower
                for phrase in [
                    "do not have enough information",
                    "don't have enough information",
                    "insufficient evidence",
                    "source documents needed",
                    "no source documents",
                    "not enough evidence",
                ]
            )
        )

        # -----------------------------------------------------
        # 9. Final request observability
        # -----------------------------------------------------

        total_ms = (
            time.perf_counter() - total_start
        ) * 1000

        log_event(
            logger,
            "request_completed",
            request_id=request_id,
            route="rag",
            source_count=len(sources),
            retrieval_ms=round(retrieval_ms, 2),
            llm_ms=round(llm_ms, 2),
            total_ms=round(total_ms, 2),
            abstained=abstained,
            status="success",
        )

        return {
            "answer": answer,
            "sources": sources,
            "route": "rag",
        }

    except Exception as exc:
        total_ms = (
            time.perf_counter() - total_start
        ) * 1000

        log_event(
            logger,
            "request_failed",
            request_id=request_id,
            error_type=type(exc).__name__,
            total_ms=round(total_ms, 2),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )