from pathlib import Path
import hashlib
import subprocess

from repo_assist.models.repository_model import FileInfo, GitInfo


class RepositoryReader:

    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "target",
        "build",
        "dist",
    }

    LANGUAGE_BY_SUFFIX = {
        ".py": "Python",
        ".java": "Java",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
    }

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)

    def discover_files(self) -> tuple[list[FileInfo], int]:
        files = []
        number_of_directories = self._traverse_dir(
            self.repository_path,
            files
        )
        return files, number_of_directories

    def _traverse_dir(self, path: Path, files: list[FileInfo]) -> int:
        directory_count = 0

        for entry in path.iterdir():
            if entry.name in self.IGNORED_DIRECTORIES:
                continue

            if entry.is_file():
                number_of_lines = self.count_lines_in_file(entry)
                language = self.find_language(entry)

                try:
                    content_hash = self.calculate_content_hash(entry)
                except (OSError, UnicodeError):
                    continue

                files.append(
                    FileInfo(
                        path=entry.relative_to(self.repository_path),
                        number_of_lines=number_of_lines,
                        language=language,
                        content_hash=content_hash,
                    )
                )

            elif entry.is_dir():
                directory_count += 1
                directory_count += self._traverse_dir(entry, files)

        return directory_count

    def find_language(self, file_path: Path) -> str | None:
        suffix = file_path.suffix.lower()
        return self.LANGUAGE_BY_SUFFIX.get(suffix)

    def count_lines_in_file(self, file_path: Path) -> int:
        try:
            with file_path.open(
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:
                return sum(1 for _ in file)
        except (OSError, UnicodeError):
            return 0

    def calculate_content_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()

        with file_path.open("rb") as file:
            for byte_block in iter(
                lambda: file.read(4096),
                b""
            ):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def get_git_info(self) -> GitInfo:
        is_git_repo = (self.repository_path / ".git").is_dir()

        if not is_git_repo:
            return GitInfo(
                is_git_repo=False,
                branch=None
            )

        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=self.repository_path,
        )

        branch_name = (
            branch.stdout.strip()
            if branch.returncode == 0
            else None
        )

        return GitInfo(
            is_git_repo=True,
            branch=branch_name
        )

    def get_repository_description(self) -> str | None:
        readme_files = [
            "README.md",
            "README.txt",
            "README",
        ]

        for readme in readme_files:
            readme_path = self.repository_path / readme

            if not readme_path.is_file():
                continue

            try:
                with readme_path.open(
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:
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