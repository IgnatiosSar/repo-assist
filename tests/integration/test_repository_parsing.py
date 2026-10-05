from pathlib import Path

from repo_assist.services.parsing_service import ParsingService
from repo_assist.repositories.repository_reader import RepositoryReader


def test_repository_files_are_parsed_into_code_chunks(tmp_path: Path):
    java_file = tmp_path / "UserService.java"
    java_file.write_text(
        """\
public class UserService {

    public void createUser() {
        System.out.println("Creating user");
    }

    public void deleteUser() {
        System.out.println("Deleting user");
    }
}
"""
    )

    repository_reader = RepositoryReader(str(tmp_path))

    files, directories_count = repository_reader.discover_files()

    parsing_service = ParsingService()

    chunks = []
    for file_info in files:
        file_chunks = parsing_service.parse_file(file_info, tmp_path)
        chunks.extend(file_chunks)

    assert directories_count == 0
    assert len(files) == 1
    assert len(chunks) == 2

    symbols = {chunk.symbol for chunk in chunks}

    assert symbols == {"createUser", "deleteUser"}

    for chunk in chunks:
        assert chunk.language == "Java"
        assert chunk.path == Path("UserService.java")
        assert chunk.parent_symbol == "UserService"