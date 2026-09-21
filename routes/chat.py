import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)
from llm.azure_openai import (
    get_openai_client,
    get_embedding_client,
)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    company: str | None = None
    year: int | None = None

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Initialize vector store and retriever
        vector_store = AzureAISearchVectorStore(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
        )
        embeddings = get_embedding_client()

        retriever = DenseRetriever(
            vector_store.client,
             embeddings,
        )

        # Retrieve relevant context
        context = ""
        if request.company and request.year:
            docs = retriever.invoke(
                query=request.question,
                company=request.company,
                year=request.year,
                top_k=5
            )
        else:
            docs = retriever.invoke(
                query=request.question,
                top_k=5
            )
        context_blocks = []
        sources = []

        for citation_id, doc in enumerate(docs, start=1):
            metadata = doc.metadata

            context_blocks.append(
                f"[Source {citation_id}]\n"
                f"{doc.page_content}"
            )
       

            sources.append(
               {
                "citation_id": citation_id,
                "document_id": metadata.get("document_id"),
                "company": metadata.get("company"),
                "ticker": metadata.get("ticker"),
                "year": metadata.get("year"),
                "filing_type": metadata.get("filing_type"),
                "source_file": metadata.get("source_file"),
                "chunk_index": metadata.get("chunk_index"),
                "rank": metadata.get("rank"),
                "evidence": doc.page_content,
               }
            )
        context = "\n\n".join(context_blocks)

        # Build chat prompt – include retrieved context and the user question
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
        Context:
        {context}

        User Question:
        {request.question}

        Answer:
         """
        client = get_openai_client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        return {"answer": answer, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
