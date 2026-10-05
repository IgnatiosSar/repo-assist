from dataclasses import dataclass
from pathlib import Path

@dataclass
class IdentityInfo:
    name: str
    path: str

@dataclass
class GitInfo:
    is_git_repo: bool
    branch: str | None

@dataclass
class RepoStats:
    files_count: int
    directories_count: int
    lines_count: int

@dataclass
class LanguageInfo:
    files_count: int
    lines_count: int
    percentage_of_total_lines: float

@dataclass
class RepositoryInfo:
    identity: IdentityInfo
    git_info: GitInfo
    stats: RepoStats
    languages: dict[str,LanguageInfo]
    description: str | None


@dataclass
class FileInfo:
    path: Path
    number_of_lines: int
    language: str | None
    content_hash: str
    