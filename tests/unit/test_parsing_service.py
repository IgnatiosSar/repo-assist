
from pathlib import Path

from repo_assist.models.repository_model import FileInfo
from repo_assist.services.parsing_service import ParsingService
from tests.helper import calculate_test_hash




def test_parse_all_files_skips_unsupported_languages(tmp_path: Path):
    java_file = tmp_path / "UserService.java"
    java_file.write_text(
        """\
public class UserService {

    public void createUser() {
        System.out.println("Creating user");
    }
}
"""
    )

    python_file = tmp_path / "user_service.py"
    python_file.write_text(
        """\
def create_user():
    print("Creating user")
"""
    )

    files = [
        FileInfo(
            path=Path("UserService.java"),
            number_of_lines=7,
            language="Java",
            content_hash=calculate_test_hash(java_file)
        ),
        FileInfo(
            path=Path("user_service.py"),
            number_of_lines=3,
            language="Python",
            content_hash=calculate_test_hash(python_file)
        ),
    ]

    service = ParsingService()
    chunks = []
    for file_info in files:
        file_chunks = service.parse_file(file_info, tmp_path)
        chunks.extend(file_chunks)

    assert len(chunks) == 1

    assert chunks[0].symbol == "createUser"
    assert chunks[0].parent_symbol == "UserService"
    assert chunks[0].language == "Java"
    assert chunks[0].path == Path("UserService.java")   