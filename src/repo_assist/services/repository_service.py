from pathlib import Path

from repo_assist.models.repository_model import (
    RepositoryInfo,
    IdentityInfo,
    RepoStats,
    LanguageInfo,
)
from repo_assist.repositories.repository_reader import RepositoryReader


class RepositoryService:

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository path '{repository_path}' does not exist."
            )

        if not self.repository_path.is_dir():
            raise NotADirectoryError(
                f"Repository path '{repository_path}' is not a directory."
            )

        self.reader = RepositoryReader(repository_path)

    def inspect_repository(self) -> RepositoryInfo:
        identity_info = self.get_identity_info()
        git_info = self.reader.get_git_info()
        repository_stats, language_info = self.get_stats()
        description = self.reader.get_repository_description()

        return RepositoryInfo(
            identity=identity_info,
            git_info=git_info,
            stats=repository_stats,
            languages=language_info,
            description=description,
        )

    def get_identity_info(self) -> IdentityInfo:
        resolved_path = self.repository_path.resolve()

        return IdentityInfo(
            name=resolved_path.name,
            path=str(resolved_path),
        )

    def get_stats(self) -> tuple[RepoStats, dict[str, LanguageInfo]]:
        files, directories_count = self.reader.discover_files()

        files_count = len(files)
        lines_count = sum(
            file.number_of_lines
            for file in files
        )

        language_info = self.get_language_info(
            files,
            lines_count
        )

        return (
            RepoStats(
                files_count=files_count,
                directories_count=directories_count,
                lines_count=lines_count,
            ),
            language_info,
        )

    def get_language_info(
        self,
        files,
        lines_count: int
    ) -> dict[str, LanguageInfo]:

        language_info = {}

        for file in files:
            if file.language is None:
                continue

            if file.language not in language_info:
                language_info[file.language] = LanguageInfo(
                    files_count=0,
                    lines_count=0,
                    percentage_of_total_lines=0.0,
                )

            language_info[file.language].files_count += 1
            language_info[file.language].lines_count += (
                file.number_of_lines
            )

        for info in language_info.values():
            info.percentage_of_total_lines = (
                info.lines_count / lines_count * 100
                if lines_count > 0
                else 0.0
            )

        return language_info