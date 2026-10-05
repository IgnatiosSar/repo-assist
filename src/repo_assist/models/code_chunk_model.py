from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodeChunk:
    content: str
    path: Path
    language: str
    symbol: str | None
    start_line: int
    end_line: int
    parent_symbol: str | None