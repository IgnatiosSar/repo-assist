from pathlib import Path

from repo_assist.repositories.sqlite_index_store import SQLiteIndexStore
from repo_assist.repositories.repository_reader import RepositoryReader
from repo_assist.services.indexing_service import IndexingService
from repo_assist.services.parsing_service import ParsingService


def create_test_repository(tmp_path: Path) -> Path:
    repository_path = tmp_path / "test-repo"
    repository_path.mkdir()

    src_path = repository_path / "src"
    src_path.mkdir()

    java_file = src_path / "UserService.java"

    java_file.write_text(
        """\
public class UserService {

    public void createUser() {
        System.out.println("Creating user");
    }
}
""",
        encoding="utf-8",
    )

    return repository_path

def test_first_indexing_indexes_repository(tmp_path: Path):
    repository_path = create_test_repository(tmp_path)

    reader = RepositoryReader(str(repository_path))

    files, _ = reader.discover_files()

    store = SQLiteIndexStore(
        tmp_path / "index.db"
    )

    parsing_service = ParsingService()

    indexing_service = IndexingService(
        index_store=store,
        parsing_service=parsing_service,
    )

    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    repo_id = store.get_repo(repository_path)

    assert repo_id is not None

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 1
    assert indexed_files[0].path == Path(
        "src/UserService.java"
    )

    row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert row is not None

    file_id = row["id"]

    chunks = store.get_chunks_for_file(file_id)

    assert len(chunks) == 1
    assert chunks[0].symbol == "createUser"
    assert chunks[0].parent_symbol == "UserService"
    assert chunks[0].language == "Java"
    assert chunks[0].path == Path("src/UserService.java")

def test_second_indexing_does_not_duplicate_unchanged_files(tmp_path: Path):
    repository_path = create_test_repository(tmp_path)

    reader = RepositoryReader(str(repository_path))
    files, _ = reader.discover_files()

    store = SQLiteIndexStore(tmp_path / "index.db")
    parsing_service = ParsingService()

    indexing_service = IndexingService(
        index_store=store,
        parsing_service=parsing_service,
    )

    # First indexing
    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    repo_id = store.get_repo(repository_path)

    assert repo_id is not None

    files_after_first_indexing = store.get_all_files(repo_id)

    assert len(files_after_first_indexing) == 1

    row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert row is not None

    file_id = row["id"]

    chunks_after_first_indexing = store.get_chunks_for_file(file_id)

    assert len(chunks_after_first_indexing) == 1

    # Second indexing — nothing has changed
    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    files_after_second_indexing = store.get_all_files(repo_id)

    assert len(files_after_second_indexing) == 1

    row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert row is not None

    file_id_after_second_indexing = row["id"]

    chunks_after_second_indexing = store.get_chunks_for_file(
        file_id_after_second_indexing
    )

    assert len(chunks_after_second_indexing) == 1

    assert file_id_after_second_indexing == file_id

def test_changed_file_replaces_old_index(tmp_path: Path):
    repository_path = create_test_repository(tmp_path)

    reader = RepositoryReader(str(repository_path))
    files, _ = reader.discover_files()

    store = SQLiteIndexStore(tmp_path / "index.db")
    parsing_service = ParsingService()

    indexing_service = IndexingService(
        index_store=store,
        parsing_service=parsing_service,
    )

    # First indexing
    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    repo_id = store.get_repo(repository_path)

    assert repo_id is not None

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 1

    old_file = indexed_files[0]
    old_hash = old_file.content_hash

    old_row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert old_row is not None

    old_file_id = old_row["id"]

    old_chunks = store.get_chunks_for_file(old_file_id)

    assert len(old_chunks) == 1
    assert old_chunks[0].symbol == "createUser"

    # Change the file
    java_file = repository_path / "src" / "UserService.java"

    java_file.write_text(
        """\
public class UserService {

    public void updateUser() {
        System.out.println("Updating user");
    }
}
""",
        encoding="utf-8",
    )

    # Rediscover the repository after the change
    updated_files, _ = reader.discover_files()

    # Second indexing
    indexing_service.index_repository(
        current_files=updated_files,
        repo_path=repository_path,
    )

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 1

    updated_file = indexed_files[0]

    assert updated_file.path == Path("src/UserService.java")
    assert updated_file.content_hash != old_hash

    new_row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert new_row is not None

    new_file_id = new_row["id"]

    new_chunks = store.get_chunks_for_file(new_file_id)

    assert len(new_chunks) == 1
    assert new_chunks[0].symbol == "updateUser"
    assert new_chunks[0].parent_symbol == "UserService"

def test_deleted_file_is_removed_from_index(tmp_path: Path):
    repository_path = create_test_repository(tmp_path)

    reader = RepositoryReader(str(repository_path))
    files, _ = reader.discover_files()

    store = SQLiteIndexStore(tmp_path / "index.db")
    parsing_service = ParsingService()

    indexing_service = IndexingService(
        index_store=store,
        parsing_service=parsing_service,
    )

    # First indexing
    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    repo_id = store.get_repo(repository_path)

    assert repo_id is not None

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 1

    row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert row is not None

    file_id = row["id"]

    chunks = store.get_chunks_for_file(file_id)

    assert len(chunks) == 1

    # Delete the file from the repository
    java_file = repository_path / "src" / "UserService.java"
    java_file.unlink()

    # Rediscover the repository
    updated_files, _ = reader.discover_files()

    assert updated_files == []

    # Second indexing
    indexing_service.index_repository(
        current_files=updated_files,
        repo_path=repository_path,
    )

    indexed_files = store.get_all_files(repo_id)

    assert indexed_files == []

    # Verify that the chunks were deleted through the foreign-key cascade
    chunk_rows = store.connection.execute(
        """
        SELECT *
        FROM chunks
        WHERE file_id = ?
        """,
        (file_id,),
    ).fetchall()

    assert chunk_rows == []


def test_mixed_file_changes_are_indexed_correctly(tmp_path: Path):
    repository_path = create_test_repository(tmp_path)

    # Add a second file that will later be deleted.
    product_file = repository_path / "src" / "ProductService.java"

    product_file.write_text(
        """\
public class ProductService {

    public void createProduct() {
        System.out.println("Creating product");
    }
}
""",
        encoding="utf-8",
    )

    reader = RepositoryReader(str(repository_path))
    files, _ = reader.discover_files()

    store = SQLiteIndexStore(tmp_path / "index.db")
    parsing_service = ParsingService()

    indexing_service = IndexingService(
        index_store=store,
        parsing_service=parsing_service,
    )

    # First indexing
    indexing_service.index_repository(
        current_files=files,
        repo_path=repository_path,
    )

    repo_id = store.get_repo(repository_path)

    assert repo_id is not None

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 2

    # Change UserService.java
    user_file = repository_path / "src" / "UserService.java"

    user_file.write_text(
        """\
public class UserService {

    public void updateUser() {
        System.out.println("Updating user");
    }
}
""",
        encoding="utf-8",
    )

    # Delete ProductService.java
    product_file.unlink()

    # Add OrderService.java
    order_file = repository_path / "src" / "OrderService.java"

    order_file.write_text(
        """\
public class OrderService {

    public void createOrder() {
        System.out.println("Creating order");
    }
}
""",
        encoding="utf-8",
    )

    # Rediscover repository after all changes
    updated_files, _ = reader.discover_files()

    # Second indexing
    indexing_service.index_repository(
        current_files=updated_files,
        repo_path=repository_path,
    )

    indexed_files = store.get_all_files(repo_id)

    assert len(indexed_files) == 2

    indexed_paths = {file.path for file in indexed_files}

    assert indexed_paths == {
        Path("src/UserService.java"),
        Path("src/OrderService.java"),
    }

    # Verify UserService was changed
    user_row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/UserService.java"),
    ).fetchone()

    assert user_row is not None

    user_chunks = store.get_chunks_for_file(user_row["id"])

    assert len(user_chunks) == 1
    assert user_chunks[0].symbol == "updateUser"

    # Verify OrderService was added
    order_row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/OrderService.java"),
    ).fetchone()

    assert order_row is not None

    order_chunks = store.get_chunks_for_file(order_row["id"])

    assert len(order_chunks) == 1
    assert order_chunks[0].symbol == "createOrder"

    # Verify ProductService was deleted
    product_row = store.connection.execute(
        """
        SELECT id
        FROM files
        WHERE repository_id = ?
          AND path = ?
        """,
        (repo_id, "src/ProductService.java"),
    ).fetchone()

    assert product_row is None