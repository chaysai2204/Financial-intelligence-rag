import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from routes.chat import ChatRequest
from routes.ingestion import router as ingestion_router


# ---------------------------------------------------------
# Chat input validation
# ---------------------------------------------------------

def test_empty_question_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(
            question="   ",
        )


def test_question_over_max_length_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(
            question="a" * 4001,
        )


def test_invalid_year_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(
            question="What was Apple revenue?",
            company="Apple",
            year=1900,
        )


def test_valid_chat_request():
    request = ChatRequest(
        question="  What was Apple revenue in 2024?  ",
        company="Apple",
        year=2024,
    )

    # Validator should also strip surrounding whitespace.
    assert request.question == "What was Apple revenue in 2024?"
    assert request.year == 2024


# ---------------------------------------------------------
# Upload validation
# ---------------------------------------------------------

app = FastAPI()
app.include_router(
    ingestion_router,
    prefix="/api",
)

client = TestClient(app)


def test_non_pdf_upload_is_rejected():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "notes.txt",
                b"not a pdf",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF files are supported."
    )


def test_empty_pdf_is_rejected():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded file is empty."
    )