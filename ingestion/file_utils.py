import hashlib
from pathlib import Path


def compute_file_hash(file_path: str | Path) -> str:
    """Compute the SHA-256 hash of a file."""

    file_path = Path(file_path)
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()