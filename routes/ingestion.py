
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from langchain_openai import AzureOpenAIEmbeddings

from ingestion.ingest_documents import ingest_document
from vectorstore.azure_ai_search import AzureAISearchVectorStore

router = APIRouter()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/octet-stream",
}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A file name is required.",
        )

    safe_filename = Path(file.filename).name

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    if (
        file.content_type
        and file.content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    upload_dir = Path("data/raw_pdfs")
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = upload_dir / safe_filename

    bytes_written = 0

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                bytes_written += len(chunk)

                if bytes_written > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded PDF exceeds the 50 MB limit.",
                    )

                buffer.write(chunk)

        if bytes_written == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        embeddings = AzureOpenAIEmbeddings(
            model=os.getenv(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            ),
            azure_endpoint=os.getenv(
                "AZURE_OPENAI_ENDPOINT"
            ),
            api_key=os.getenv(
                "AZURE_OPENAI_API_KEY"
            ),
            api_version=os.getenv(
                "AZURE_OPENAI_API_VERSION"
            ),
        )

        vector_store = AzureAISearchVectorStore(
            endpoint=os.getenv(
                "AZURE_SEARCH_ENDPOINT"
            ),
            api_key=os.getenv(
                "AZURE_SEARCH_API_KEY"
            ),
            index_name=os.getenv(
                "AZURE_SEARCH_INDEX_NAME"
            ),
        )

        ingest_document(
            pdf_path=str(file_path),
            embeddings=embeddings,
            vector_store=vector_store,
        )

    except HTTPException:
        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as exc:
        print(
            f"Upload failed: "
            f"{type(exc).__name__}: {exc}"
        )

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Document processing failed.",
        )

    finally:
        await file.close()

    return {
        "message": "Document uploaded successfully",
        "file_name": safe_filename,
    }