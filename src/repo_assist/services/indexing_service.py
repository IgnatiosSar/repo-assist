from repo_assist.models.repository_model import FileInfo
from repo_assist.services.parsing_service import ParsingService
from repo_assist.repositories.index_store import IndexStore
from pathlib import Path

from repo_assist.services.repository_service import RepositoryService

class IndexingService:

    def __init__(self, index_store: IndexStore, parsing_service: ParsingService):
        self.index_store = index_store
        self.parsing_service = parsing_service

    def index_repository(self, current_files: list[FileInfo], repo_path: Path):
        repo_id = self.index_store.get_repo(repo_path)
        if repo_id is None:
            repository_service = RepositoryService(repo_path)
            repo_info = repository_service.inspect_repository()
            repo_id = self.index_store.save_repo(repo_info)


        new_files = []
        changed_files = []
        deleted_files = []

        indexed_files = self.index_store.get_all_files(repo_id)

        indexed_by_path = {
            file.path: file
            for file in indexed_files
        }

        # Classify current files
        for file_info in current_files:
            indexed_file_info = indexed_by_path.get(file_info.path)

            if indexed_file_info is None:
                new_files.append(file_info)
            elif not self.compare_files(file_info, indexed_file_info):
                changed_files.append(file_info)

        # Find deleted files
        current_file_paths = {
            file.path
            for file in current_files
        }

        for indexed_file_info in indexed_files:
            if indexed_file_info.path not in current_file_paths:
                deleted_files.append(indexed_file_info)

        # Delete old indexed representations
        files_to_delete = deleted_files + changed_files

        for file_info in files_to_delete:
            self.index_store.delete_file(repo_id,file_info.path)

        # Index new and changed files
        files_to_index = new_files + changed_files

        for file_info in files_to_index:
            code_chunks = self.parsing_service.parse_file(file_info, repo_path)

            file_id = self.index_store.save_file(repo_id, file_info)

            self.index_store.save_chunks(
                code_chunks,
                file_id
            )

    def compare_files(self, file_info: FileInfo,  indexed_file_info: FileInfo) -> bool:
        return file_info.content_hash == indexed_file_info.content_hash
