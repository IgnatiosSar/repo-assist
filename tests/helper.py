import hashlib
from pathlib import Path

def calculate_test_hash(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()