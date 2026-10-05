from pathlib import Path

import pytest

from repo_assist.services.repository_service import RepositoryService


def test_inspect_python_repository(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "print('hello')\nprint('world')\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Test Repository\n\nA test repository.\n",
        encoding="utf-8",
    )

    service = RepositoryService(str(tmp_path))

    repository_info = service.inspect_repository()

    assert repository_info.identity.name == tmp_path.name
    assert repository_info.identity.path == str(tmp_path.resolve())

    assert repository_info.stats.files_count == 2
    assert repository_info.stats.lines_count == 5

    assert repository_info.languages["Python"].files_count == 1
    assert repository_info.languages["Python"].lines_count == 2

    assert repository_info.description == "A test repository."


def test_inspect_nested_repository(tmp_path: Path):
    nested_dir = tmp_path / "src" / "repo"
    nested_dir.mkdir(parents=True)

    (nested_dir / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    service = RepositoryService(str(tmp_path))

    repository_info = service.inspect_repository()

    assert repository_info.stats.files_count == 1
    assert repository_info.stats.directories_count == 2
    assert repository_info.stats.lines_count == 1


def test_detect_multiple_languages(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )
    (tmp_path / "Main.java").write_text(
        "class Main {}\n",
        encoding="utf-8",
    )

    service = RepositoryService(str(tmp_path))

    repository_info = service.inspect_repository()

    assert repository_info.stats.files_count == 2

    assert repository_info.languages["Python"].files_count == 1
    assert repository_info.languages["Python"].lines_count == 1

    assert repository_info.languages["Java"].files_count == 1
    assert repository_info.languages["Java"].lines_count == 1


def test_non_existing_repository_raises_error(tmp_path: Path):
    repository_path = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError):
        RepositoryService(str(repository_path))


def test_file_as_repository_path_raises_error(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("content", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        RepositoryService(str(file_path))