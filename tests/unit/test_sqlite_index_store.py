import sqlite3
from pathlib import Path

import pytest

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import (
    FileInfo,
    GitInfo,
    IdentityInfo,
    RepoStats,
    RepositoryInfo,
)
from repo_assist.repositories.sqlite_index_store import SQLiteIndexStore


def create_repository_info(repository_path: Path) -> RepositoryInfo:
    return RepositoryInfo(
        identity=IdentityInfo(
            name=repository_path.name,
            path=str(repository_path),
        ),
        git_info=GitInfo(
            is_git_repo=True,
            branch="main",
        ),
        stats=RepoStats(
            files_count=1,
            directories_count=0,
            lines_count=10,
        ),
        languages={},
        description=None,
    )


def create_file_info(
    path: Path,
    content_hash: str = "hash123",
) -> FileInfo:
    return FileInfo(
        path=path,
        number_of_lines=10,
        language="Python",
        content_hash=content_hash,
    )


def create_chunk(path: Path) -> CodeChunk:
    return CodeChunk(
        content="def hello():\n    print('hello')",
        path=path,
        language="Python",
        symbol="hello",
        start_line=1,
        end_line=2,
        parent_symbol=None,
    )


def create_store(tmp_path: Path) -> SQLiteIndexStore:
    return SQLiteIndexStore(tmp_path / "test.db")


def test_save_and_get_repository(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_info = create_repository_info(repository_path)

    repo_id = store.save_repo(repo_info)

    result = store.get_repo(repository_path)

    assert result == repo_id


def test_get_repository_returns_none_when_not_indexed(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"

    result = store.get_repo(repository_path)

    assert result is None


def test_save_and_get_file(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    file_id = store.save_file(
        repo_id,
        file_info,
    )

    result = store.get_file(
        repo_id,
        file_info.path,
    )

    assert result == file_info
    assert file_id is not None


def test_get_file_returns_none_when_not_indexed(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    result = store.get_file(
        repo_id,
        Path("src/main.py"),
    )

    assert result is None


def test_get_all_files(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    first_file = create_file_info(
        Path("src/main.py"),
        "hash1",
    )

    second_file = create_file_info(
        Path("src/service.py"),
        "hash2",
    )

    store.save_file(repo_id, first_file)
    store.save_file(repo_id, second_file)

    result = store.get_all_files(repo_id)

    assert len(result) == 2
    assert first_file in result
    assert second_file in result


def test_delete_file(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    store.save_file(repo_id, file_info)

    store.delete_file(
        repo_id,
        file_info.path,
    )

    result = store.get_file(
        repo_id,
        file_info.path,
    )

    assert result is None


def test_save_and_get_chunks(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    file_id = store.save_file(
        repo_id,
        file_info,
    )

    chunk = create_chunk(file_info.path)

    store.save_chunks(
        [chunk],
        file_id,
    )

    result = store.get_chunks_for_file(file_id)

    assert result == [chunk]


def test_delete_file_cascades_to_chunks(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    file_id = store.save_file(
        repo_id,
        file_info,
    )

    chunk = create_chunk(file_info.path)

    store.save_chunks(
        [chunk],
        file_id,
    )

    store.delete_file(
        repo_id,
        file_info.path,
    )

    result = store.get_chunks_for_file(file_id)

    assert result == []


def test_fts_index_tracks_chunk_insert_and_file_deletion(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )
    file_info = create_file_info(Path("src/main.py"))
    file_id = store.save_file(repo_id, file_info)
    chunk = create_chunk(file_info.path)

    store.save_chunks([chunk], file_id)

    inserted_rows = store.connection.execute(
        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?",
        ("hello",),
    ).fetchall()
    assert len(inserted_rows) == 1

    store.delete_file(repo_id, file_info.path)

    remaining_rows = store.connection.execute(
        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?",
        ("hello",),
    ).fetchall()
    assert remaining_rows == []


def test_search_chunks_returns_matching_chunks_from_repository(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )
    file_info = create_file_info(Path("src/main.py"))
    file_id = store.save_file(repo_id, file_info)
    chunk = create_chunk(file_info.path)
    store.save_chunks([chunk], file_id)

    results = store.search_chunks(repo_id, "hello", top_k=5)

    assert results == [chunk]


def test_search_chunks_respects_top_k_limit(tmp_path: Path):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )
    file_info = create_file_info(Path("src/main.py"))
    file_id = store.save_file(repo_id, file_info)
    chunks = [
        CodeChunk(
            content=f"def hello_{index}(): return 'hello'",
            path=file_info.path,
            language="Python",
            symbol=f"hello_{index}",
            start_line=index,
            end_line=index,
            parent_symbol=None,
        )
        for index in range(1, 4)
    ]
    store.save_chunks(chunks, file_id)

    results = store.search_chunks(repo_id, "hello", top_k=2)

    assert len(results) == 2


def test_search_chunks_isolated_to_requested_repository(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    first_repository = tmp_path / "repo-one"
    first_repo_id = store.save_repo(
        create_repository_info(first_repository)
    )
    first_file = create_file_info(Path("src/main.py"))
    first_file_id = store.save_file(first_repo_id, first_file)
    first_chunk = create_chunk(first_file.path)
    store.save_chunks([first_chunk], first_file_id)

    second_repository = tmp_path / "repo-two"
    second_repo_id = store.save_repo(
        create_repository_info(second_repository)
    )
    second_file = create_file_info(Path("src/main.py"))
    second_file_id = store.save_file(second_repo_id, second_file)
    second_chunk = CodeChunk(
        content="def hello(): return 'hello from another repository'",
        path=second_file.path,
        language="Python",
        symbol="hello",
        start_line=1,
        end_line=1,
        parent_symbol=None,
    )
    store.save_chunks([second_chunk], second_file_id)

    results = store.search_chunks(first_repo_id, "hello", top_k=5)

    assert results == [first_chunk]


def test_search_chunks_returns_empty_list_when_no_chunks_match(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )
    file_info = create_file_info(Path("src/main.py"))
    file_id = store.save_file(repo_id, file_info)
    store.save_chunks([create_chunk(file_info.path)], file_id)

    results = store.search_chunks(repo_id, "nonexistent", top_k=5)

    assert results == []


def test_duplicate_repository_path_is_rejected(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_info = create_repository_info(repository_path)

    store.save_repo(repo_info)

    with pytest.raises(sqlite3.IntegrityError):
        store.save_repo(repo_info)


def test_duplicate_file_path_in_same_repository_is_rejected(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    repository_path = tmp_path / "my-repo"
    repo_id = store.save_repo(
        create_repository_info(repository_path)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    store.save_file(repo_id, file_info)

    with pytest.raises(sqlite3.IntegrityError):
        store.save_file(repo_id, file_info)


def test_same_file_path_allowed_in_different_repositories(
    tmp_path: Path,
):
    store = create_store(tmp_path)

    first_repository = tmp_path / "repo-one"
    second_repository = tmp_path / "repo-two"

    first_repo_id = store.save_repo(
        create_repository_info(first_repository)
    )

    second_repo_id = store.save_repo(
        create_repository_info(second_repository)
    )

    file_info = create_file_info(
        Path("src/main.py")
    )

    first_file_id = store.save_file(
        first_repo_id,
        file_info,
    )

    second_file_id = store.save_file(
        second_repo_id,
        file_info,
    )

    assert first_file_id != second_file_id
