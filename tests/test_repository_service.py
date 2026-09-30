import pytest

from repo_assist.services.repository_service import RepositoryService


def test_inspect_python_repository(tmp_path):
    (tmp_path / "main.py").write_text(
        "print('hello')\n"
        "print('world')\n"
    )

    (tmp_path / "utils.py").write_text(
        "def add(a, b):\n"
        "    return a + b\n"
    )

    service = RepositoryService(tmp_path)

    result = service.inspect_repository()

    assert result.identity.name == tmp_path.name
    assert result.identity.path == str(tmp_path.resolve())

    assert result.stats.files_count == 2
    assert result.stats.directories_count == 0
    assert result.stats.lines_count == 4

    assert result.languages["Python"].files_count == 2
    assert result.languages["Python"].lines_count == 4
    assert result.languages["Python"].percentage_of_total_lines == 100.0


def test_inspect_nested_repository(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    (tmp_path / "main.py").write_text("print('hello')\n")
    (src / "utils.py").write_text("print('utils')\n")

    service = RepositoryService(tmp_path)

    result = service.inspect_repository()

    assert result.stats.files_count == 2
    assert result.stats.directories_count == 1
    assert result.stats.lines_count == 2


def test_detect_multiple_languages(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n")
    (tmp_path / "App.java").write_text("class App {}\n")
    (tmp_path / "script.js").write_text("console.log('hello');\n")

    service = RepositoryService(tmp_path)

    result = service.inspect_repository()

    assert result.stats.files_count == 3

    assert result.languages["Python"].files_count == 1
    assert result.languages["Java"].files_count == 1
    assert result.languages["JavaScript"].files_count == 1


def test_ignored_directories_are_not_counted(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n")

    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "fake.py").write_text("print('ignored')\n")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "fake.js").write_text("console.log('ignored');\n")

    service = RepositoryService(tmp_path)

    result = service.inspect_repository()

    assert result.stats.files_count == 1
    assert result.stats.lines_count == 1
    assert "JavaScript" not in result.languages


def test_non_existing_repository_raises_error(tmp_path):
    repository_path = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError):
        RepositoryService(repository_path)


def test_file_as_repository_path_raises_error(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello\n")

    with pytest.raises(NotADirectoryError):
        RepositoryService(file_path)


def test_non_git_repository(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n")

    service = RepositoryService(tmp_path)

    result = service.inspect_repository()

    assert result.git_info.is_git_repo is False
    assert result.git_info.branch is None