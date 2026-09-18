import os
import re
import json

import openai
from dotenv import load_dotenv
from openai import AzureOpenAI
from pydantic import BaseModel
from langchain_openai import AzureOpenAIEmbeddings


load_dotenv()


def get_openai_client() -> AzureOpenAI:
    """
    Create Azure OpenAI client.

    Returns:
        Azure OpenAI client.
    """
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def get_embedding_client() -> AzureOpenAIEmbeddings:
    """
    Create the Azure OpenAI embedding client.

    The same embedding configuration is used for
    document indexing and query-time dense retrieval.

    Returns:
        Azure OpenAI embeddings client.
    """
    return AzureOpenAIEmbeddings(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def get_structured_completion(
    prompt: str,
    response_model: type[BaseModel],
    model: str | None = None,
) -> BaseModel:
    """
    Generate structured output.

    Args:
        prompt: Input prompt.
        response_model: Pydantic response model.
        model: Azure OpenAI deployment name.

    Returns:
        Parsed response model.
    """

    # Read deployment name from environment when not provided;
    # do not fallback to a hardcoded name.
    model = model or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    client = get_openai_client()

    messages = [
        {
            "role": "system",
            "content": "You are an expert financial analyst.",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # Prefer structured parsing when supported by the deployment.
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_model,
        )

        # Debug: show structured parsed output.
        try:
            parsed = response.choices[0].message.parsed
            print("[debug] Structured parsed output:", parsed)
        except Exception:
            print(
                "[debug] Structured response received "
                "but could not access parsed field"
            )

        return response.choices[0].message.parsed

    except openai.BadRequestError as exc:
        # Fallback: some Azure deployments/models don't support
        # structured outputs.
        # Request a JSON-only response and parse it with Pydantic.

        msg = str(exc)

        if (
            "response_format" in msg
            or "json_schema" in msg
            or "Structured Outputs" in msg
        ):
            fallback = client.chat.completions.create(
                model=model,
                messages=messages,
            )

            text = fallback.choices[0].message.content

            print("[debug] Fallback raw text response:\n", text)

            # Try to extract the first JSON object from the model output.
            match = re.search(r"\{.*\}", text, re.S)
            json_text = match.group(0) if match else text

            try:
                # Handle explicit null responses.
                if (
                    isinstance(json_text, str)
                    and json_text.strip() in ("null", "None", "")
                ):
                    # Prefer Pydantic v2 model_construct.
                    if hasattr(response_model, "model_construct"):
                        return response_model.model_construct()

                    # Pydantic v1/v2 fallback.
                    try:
                        if hasattr(response_model, "model_validate"):
                            return response_model.model_validate({})

                        return response_model.parse_obj({})

                    except Exception:
                        raise RuntimeError(
                            "Model returned null and cannot construct "
                            "an empty instance; please check the model "
                            "schema or use a deployment that supports "
                            "structured outputs."
                        )

                # Pydantic v2: model_validate_json.
                # Pydantic v1 fallback: parse_raw.
                if hasattr(response_model, "model_validate_json"):
                    parsed = response_model.model_validate_json(
                        json_text
                    )
                else:
                    parsed = response_model.parse_raw(
                        json_text
                    )

                return parsed

            except Exception as e:
                raise RuntimeError(
                    "Failed to parse JSON fallback response: "
                    f"{e}\nRaw output:\n{text}"
                ) from e

        # Re-raise if it's a different bad request.
        raise