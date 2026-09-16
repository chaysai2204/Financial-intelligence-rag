import json
from pathlib import Path

from pydantic import ValidationError

from evaluation.schemas import EvaluationQuestion


DATASET_PATH = Path("evaluation/retrieval_questions.jsonl")


def validate_dataset():
    valid_count = 0

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
                EvaluationQuestion.model_validate(data)
                valid_count += 1

            except json.JSONDecodeError as error:
                print(f"Line {line_number}: invalid JSON")
                print(error)
                return

            except ValidationError as error:
                print(f"Line {line_number}: schema validation failed")
                print(error)
                return

    print(f"Validated {valid_count} evaluation questions successfully.")


if __name__ == "__main__":
    validate_dataset()