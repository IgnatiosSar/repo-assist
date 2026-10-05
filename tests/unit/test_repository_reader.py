from pathlib import Path

from repo_assist.repositories.repository_reader import RepositoryReader
from tests.helper import calculate_test_hash


def test_discover_files_returns_file_information(tmp_path: Path):
    python_file = tmp_path / "main.py"
    python_file.write_text(
        "print('hello')\nprint('world')\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    files, directories_count = reader.discover_files()

    assert directories_count == 0
    assert len(files) == 1

    file_info = files[0]

    assert file_info.path == Path("main.py")
    assert file_info.number_of_lines == 2
    assert file_info.language == "Python"
    assert file_info.content_hash == calculate_test_hash(python_file)


def test_ignored_directories_are_not_counted(tmp_path: Path):
    ignored_directory = tmp_path / "__pycache__"
    ignored_directory.mkdir()

    (ignored_directory / "cached.py").write_text(
        "print('ignored')\n",
        encoding="utf-8",
    )

    normal_directory = tmp_path / "src"
    normal_directory.mkdir()

    (normal_directory / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    files, directories_count = reader.discover_files()

    assert directories_count == 1
    assert len(files) == 1
    assert files[0].path == Path("src/main.py")


def test_same_file_content_produces_same_hash(tmp_path: Path):
    first_file = tmp_path / "first.py"
    second_file = tmp_path / "second.py"

    first_file.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )
    second_file.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    first_hash = reader.calculate_content_hash(first_file)
    second_hash = reader.calculate_content_hash(second_file)

    assert first_hash == second_hash
    assert first_hash == calculate_test_hash(first_file)


def test_changed_file_content_produces_different_hash(tmp_path: Path):
    file_path = tmp_path / "main.py"

    file_path.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    first_hash = reader.calculate_content_hash(file_path)

    file_path.write_text(
        "print('goodbye')\n",
        encoding="utf-8",
    )

    second_hash = reader.calculate_content_hash(file_path)

    assert first_hash != second_hash


def test_find_language(tmp_path: Path):
    reader = RepositoryReader(str(tmp_path))

    assert reader.find_language(Path("main.py")) == "Python"
    assert reader.find_language(Path("Main.java")) == "Java"
    assert reader.find_language(Path("unknown.xyz")) is None


def test_count_lines_in_file(tmp_path: Path):
    file_path = tmp_path / "main.py"
    file_path.write_text(
        "line 1\nline 2\nline 3\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    assert reader.count_lines_in_file(file_path) == 3


def test_non_git_repository(tmp_path: Path):
    reader = RepositoryReader(str(tmp_path))

    git_info = reader.get_git_info()

    assert git_info.is_git_repo is False
    assert git_info.branch is None


def test_repository_description_from_readme(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Test Repository\n\n"
        "This is the repository description.\n\n"
        "More content here.\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    description = reader.get_repository_description()

    assert description == "This is the repository description."


def test_discover_files_returns_relative_paths(tmp_path: Path):
    src_directory = tmp_path / "src" / "services"
    src_directory.mkdir(parents=True)

    file_path = src_directory / "user_service.py"
    file_path.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(tmp_path))

    files, _ = reader.discover_files()

    assert files[0].path == Path("src/services/user_service.py")