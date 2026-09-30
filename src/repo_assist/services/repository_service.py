from pathlib import Path
import subprocess
from repo_assist.models.repository_model import (
    RepositoryInfo,
    IdentityInfo,
    GitInfo,
    RepoStats,
    LanguageInfo,
    FileInfo
)
class RepositoryService:

    IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "target",
    "build",
    "dist",
    }   #Ignore common directories that are not relevant for repository analysis (used in traverse_files method)

    LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    } #Use this dictionary to map file suffixes to programming languages (used in find_language method)

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)
        if not self.repository_path.exists():
            raise FileNotFoundError(f"Repository path '{repository_path}' does not exist.")
        if not self.repository_path.is_dir():
            raise NotADirectoryError(f"Repository path '{repository_path}' is not a directory.")

    def inspect_repository(self) -> RepositoryInfo:
        identity_info = self.get_identity_info()
        git_info = self.get_git_info()
        repository_stats, language_info = self.get_stats()
        description = self.get_repository_description()
        repository_info = RepositoryInfo(
            identity=identity_info,
            git_info=git_info,
            stats=repository_stats,
            languages=language_info,
            description=description 
        )
        return repository_info

    def get_identity_info(self) -> IdentityInfo:
        name = self.repository_path.resolve().name
        path = self.repository_path.resolve()
        return IdentityInfo(name=name, path=str(path))

    def get_git_info(self) -> GitInfo:
        is_git_repo = (self.repository_path / ".git").is_dir()
        if is_git_repo:
            branch = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=self.repository_path)
            branch_name = branch.stdout.strip() if branch.returncode == 0 else None
            git_info = GitInfo(is_git_repo=True, branch=branch_name)
        else:
          git_info = GitInfo(is_git_repo=False, branch=None)
        return git_info

    def discover_files(self) -> tuple[list[FileInfo], int]:
        files = []
        number_of_directories = self._traverse_dir(self.repository_path, files)
        return files, number_of_directories

    def _traverse_dir(self, path: Path, files: list[FileInfo]) -> int:
        directory_count = 0
        for entry in path.iterdir():
            if entry.name in self.IGNORED_DIRECTORIES:
                continue
            if entry.is_file():
                number_of_lines = self.count_lines_in_file(entry)
                language = self.find_language(entry)
                files.append(FileInfo(path=entry, number_of_lines=number_of_lines, language=language))
            elif entry.is_dir():
                directory_count += 1
                directory_count += self._traverse_dir(entry, files)
        return directory_count


    def find_language(self, file_path: Path) -> str | None:
        suffix = file_path.suffix.lower()
        return self.LANGUAGE_BY_SUFFIX.get(suffix)

    def count_lines_in_file(self, file_path: Path) -> int:
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as file:
                return sum(1 for _ in file)
        except (OSError, UnicodeError):
            return 0

    def get_stats(self) -> tuple[RepoStats, dict[str, LanguageInfo]]:
        files, directories_count = self.discover_files()
        files_count = len(files)
        lines_count = sum(file.number_of_lines for file in files)
        language_info = self.get_language_info(files, lines_count)
        return RepoStats(files_count=files_count, directories_count=directories_count, lines_count=lines_count), language_info


    def get_language_info(self, files: list[FileInfo], lines_count: int) -> dict[str, LanguageInfo]:
        language_info = {}
        for file in files:
            if file.language is None:
                continue
            if file.language not in language_info:
                language_info[file.language] = LanguageInfo(files_count=0, lines_count=0, percentage_of_total_lines=0.0)
            language_info[file.language].files_count += 1
            language_info[file.language].lines_count += file.number_of_lines

        for _, info in language_info.items():
            info.percentage_of_total_lines = (info.lines_count / lines_count * 100) if lines_count > 0 else 0.0

        return language_info

    
    def get_repository_description(self) -> str | None:
        '''
        Take the first meaningful paragraph of README as the description. Stop when there is an empty line or a header
        '''
        readme_files = ["README.md", "README.txt", "README"]

        for readme in readme_files:
            readme_path = self.repository_path / readme

            if not readme_path.is_file():
                continue

            try:
                with readme_path.open("r", encoding="utf-8", errors="ignore") as file:
                    lines = file.readlines()
            except (OSError, UnicodeError):
                continue

            description_lines = []
            started = False

            for line in lines:
                line = line.strip()

                if not line:
                    if started:
                        break
                    continue

                if line.startswith("#"):
                    if not started:
                        continue
                    break

                description_lines.append(line)
                started = True

            if description_lines:
                return " ".join(description_lines)

        return None