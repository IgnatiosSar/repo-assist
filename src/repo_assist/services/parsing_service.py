from pathlib import Path

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo

class ParsingService:

    def parse_file(self, file_info: FileInfo, repo_path: Path) -> list[CodeChunk]:
        if file_info.language and file_info.language.lower() == "java":
            from repo_assist.parsers.java_parser import JavaCodeParser

            parser = JavaCodeParser()
            return parser.parse_file(file_info, repo_path)

        print(
            f"Unsupported language: {file_info.language} "
            f"for file: {file_info.path}"
        )
        return []