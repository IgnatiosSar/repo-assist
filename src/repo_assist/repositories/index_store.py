from abc import ABC, abstractmethod
from pathlib import Path

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo, RepositoryInfo


class IndexStore(ABC):

    # repositories

    @abstractmethod
    def get_repo(self, repo_path: Path) -> int | None:
        pass

    @abstractmethod
    def save_repo(self, repo_info: RepositoryInfo) -> int:
        pass

    # files

    @abstractmethod
    def get_file(self, repo_id: int, file_path: Path) -> FileInfo | None:
        pass

    @abstractmethod
    def get_all_files(self, repo_id: int) -> list[FileInfo]:
        pass

    @abstractmethod
    def save_file(self, repo_id: int, file_info: FileInfo) -> int:
        pass

    @abstractmethod
    def delete_file(self, repo_id: int, file_path: Path):
        pass

    # chunks

    @abstractmethod
    def save_chunks(self, code_chunks: list[CodeChunk], file_id: int):
        pass

    @abstractmethod
    def get_chunks_for_file(self, file_id: int) -> list[CodeChunk]:
        pass

    @abstractmethod
    def search_chunks(self, repo_id: int, query: str, top_k: int) -> list[CodeChunk]:
        pass