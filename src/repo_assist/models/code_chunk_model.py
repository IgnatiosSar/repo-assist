from dataclasses import dataclass


@dataclass
class CodeChunk:
    content: str
    path: str
    language: str
    symbol: str | None
    start_line: int
    end_line: int
    parent_symbol: str | None