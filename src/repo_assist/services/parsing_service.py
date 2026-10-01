from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo

class ParsingService:

    def parse_all_files(self, files: list[FileInfo]) -> list[CodeChunk]:
        all_chunks = []
        for file_info in files:
            language = file_info.language.lower()
            if language == "java":
                from repo_assist.parsers.java_parser import JavaCodeParser
                parser = JavaCodeParser()
            else:
                continue  # Skip unsupported languages for now

            file_chunks = parser.parse_file(file_info)
            all_chunks.extend(file_chunks)
        return all_chunks