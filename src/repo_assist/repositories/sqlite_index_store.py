import sqlite3
from pathlib import Path

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo, RepositoryInfo
from repo_assist.repositories.index_store import IndexStore


class SQLiteIndexStore(IndexStore):

    def __init__(self, db_path: Path):
        self.db_path = db_path

        self.connection = sqlite3.connect(self.db_path)

        self.connection.execute("PRAGMA foreign_keys = ON")

        self.connection.row_factory = sqlite3.Row

        self._create_schema()

    def _create_schema(self):
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                repository_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                number_of_lines INTEGER NOT NULL,
                language TEXT,
                content_hash TEXT NOT NULL,

                UNIQUE(repository_id, path),

                FOREIGN KEY (repository_id)
                    REFERENCES repositories(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                language TEXT,
                symbol TEXT,
                parent_symbol TEXT,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,

                FOREIGN KEY (file_id)
                    REFERENCES files(id)
                    ON DELETE CASCADE
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content,
                symbol,
                parent_symbol, 
                content ='chunks');

            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content, symbol, parent_symbol)
                VALUES (new.id, new.content, new.symbol, new.parent_symbol);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content, symbol, parent_symbol)
                VALUES('delete', old.id, old.content, old.symbol, old.parent_symbol);
            END;


            """
        )

        self.connection.commit()

    # repositories

    def get_repo(self, repo_path: Path) -> int | None:
        cursor = self.connection.execute(
            """
            SELECT id
            FROM repositories
            WHERE path = ?
            """,
            (str(repo_path.resolve()),),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["id"]

    def save_repo(self, repo_info: RepositoryInfo) -> int:
        repository_path = str(
            Path(repo_info.identity.path).resolve()
        )

        cursor = self.connection.execute(
            """
            INSERT INTO repositories (name, path)
            VALUES (?, ?)
            """,
            (
                repo_info.identity.name,
                repository_path,
            ),
        )

        self.connection.commit()

        return cursor.lastrowid

    # files

    def get_file(self, repo_id: int, file_path: Path) -> FileInfo | None:

        cursor = self.connection.execute(
            """
            SELECT path, number_of_lines, language, content_hash
            FROM files
            WHERE repository_id = ?
              AND path = ?
            """,
            (
                repo_id,
                str(file_path),
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return FileInfo(
            path=Path(row["path"]),
            number_of_lines=row["number_of_lines"],
            language=row["language"],
            content_hash=row["content_hash"],
        )

    def get_all_files(self, repo_id: int) -> list[FileInfo]:
        cursor = self.connection.execute(
            """
            SELECT path, number_of_lines, language, content_hash
            FROM files
            WHERE repository_id = ?
            """,
            (repo_id,),
        )

        return [
            FileInfo(
                path=Path(row["path"]),
                number_of_lines=row["number_of_lines"],
                language=row["language"],
                content_hash=row["content_hash"],
            )
            for row in cursor.fetchall()
        ]

    def save_file(
        self,
        repo_id: int,
        file_info: FileInfo,
    ) -> int:

        cursor = self.connection.execute(
            """
            INSERT INTO files (
                repository_id,
                path,
                number_of_lines,
                language,
                content_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                repo_id,
                str(file_info.path),
                file_info.number_of_lines,
                file_info.language,
                file_info.content_hash,
            ),
        )

        self.connection.commit()

        return cursor.lastrowid

    def delete_file( self, repo_id: int, file_path: Path):
        self.connection.execute(
            """
            DELETE FROM files
            WHERE repository_id = ?
              AND path = ?
            """,
            (
                repo_id,
                str(file_path),
            ),
        )

        self.connection.commit()

    # chunks

    def save_chunks(self, code_chunks: list[CodeChunk], file_id: int):
        self.connection.executemany(
            """
            INSERT INTO chunks (
                file_id,
                content,
                language,
                symbol,
                parent_symbol,
                start_line,
                end_line
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    file_id,
                    chunk.content,
                    chunk.language,
                    chunk.symbol,
                    chunk.parent_symbol,
                    chunk.start_line,
                    chunk.end_line,
                )
                for chunk in code_chunks
            ],
        )

        self.connection.commit()

    def get_chunks_for_file(self, file_id: int) -> list[CodeChunk]:

        cursor = self.connection.execute(
            """
            SELECT
                chunks.content,
                files.path,
                chunks.language,
                chunks.symbol,
                chunks.start_line,
                chunks.end_line,
                chunks.parent_symbol
            FROM chunks
            JOIN files
                ON chunks.file_id = files.id
            WHERE chunks.file_id = ?
            """,
            (file_id,),
        )

        return [
            CodeChunk(
                content=row["content"],
                path=Path(row["path"]),
                language=row["language"],
                symbol=row["symbol"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                parent_symbol=row["parent_symbol"],
            )
            for row in cursor.fetchall()
        ]

    def search_chunks(self, repo_id: int, query: str, top_k: int) -> list[CodeChunk]:
        cursor = self.connection.execute(
            """
            SELECT
                chunks.content,
                files.path,
                chunks.language,
                chunks.symbol,
                chunks.start_line,
                chunks.end_line,
                chunks.parent_symbol
            FROM chunks_fts
            JOIN chunks ON chunks_fts.rowid = chunks.id
            JOIN files ON chunks.file_id = files.id
            WHERE files.repository_id = ?
              AND chunks_fts MATCH ?
            ORDER BY bm25(chunks_fts)
            LIMIT ?
            """,
            (repo_id, query, top_k),
        )

        return [
            CodeChunk(
                content=row["content"],
                path=Path(row["path"]),
                language=row["language"],
                symbol=row["symbol"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                parent_symbol=row["parent_symbol"],
            )
            for row in cursor.fetchall()
        ]
        