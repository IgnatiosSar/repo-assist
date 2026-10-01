from abc import ABC, abstractmethod

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo

class CodeParser(ABC):
    @abstractmethod
    def parse_file(self, file_info: FileInfo) -> list[CodeChunk]:
        pass