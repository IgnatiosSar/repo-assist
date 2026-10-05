from pathlib import Path

from repo_assist.models.repository_model import FileInfo
from repo_assist.parsers.java_parser import JavaCodeParser
from tests.helper import calculate_test_hash

def test_parse_java_file(tmp_path: Path):
    java_file = tmp_path / "UserService.java"

    java_file.write_text(
        """\
package example;

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

    file_info = FileInfo(
        path=Path("UserService.java"),
        number_of_lines=13,
        language="Java",
        content_hash=calculate_test_hash(java_file))

    parser = JavaCodeParser()

    chunks = parser.parse_file(file_info, tmp_path)

    assert len(chunks) == 2

    assert chunks[0].symbol == "createUser"
    assert chunks[0].parent_symbol == "UserService"
    assert chunks[0].language == "Java"
    assert chunks[0].path == Path("UserService.java")
    assert chunks[0].start_line == 5
    assert chunks[0].end_line == 7
    assert "Creating user" in chunks[0].content

    assert chunks[1].symbol == "deleteUser"
    assert chunks[1].parent_symbol == "UserService"
    assert chunks[1].language == "Java"
    assert chunks[1].path == Path("UserService.java")
    assert chunks[1].start_line == 9
    assert chunks[1].end_line == 11
    assert "Deleting user" in chunks[1].content