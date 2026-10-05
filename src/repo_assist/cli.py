import typer
from pathlib import Path

from repo_assist.services.repository_service import RepositoryService
#from repo_assist.repositories.index_store import index_store
from repo_assist.repositories.repository_reader import RepositoryReader
from repo_assist.services.indexing_service import IndexingService

app = typer.Typer()


@app.command()
def info(repo_path: Path):
    service = RepositoryService(repo_path)
    repo_info = service.inspect_repository()

    print()
    print("Repository Information")
    print("────────────────────────────────")
    print(f"Name:         {repo_info.identity.name}")
    print(f"Path:         {repo_info.identity.path}")

    print()
    print("Git")
    print("────────────────────────────────")
    print(f"Repository:   {'Yes' if repo_info.git_info.is_git_repo else 'No'}")
    print(f"Branch:       {repo_info.git_info.branch or 'N/A'}")

    print()
    print("Statistics")
    print("────────────────────────────────")
    print(f"Files:        {repo_info.stats.files_count}")
    print(f"Directories:  {repo_info.stats.directories_count}")
    print(f"Lines:        {repo_info.stats.lines_count}")

    print()
    print("Languages")
    print("────────────────────────────────")

    if repo_info.languages:
        for language, info in repo_info.languages.items():
            print(
                f"{language:<14}"
                f"{info.files_count:>3} files    "
                f"{info.lines_count:>5} lines    "
                f"{info.percentage_of_total_lines:>6.2f}%"
            )
    else:
        print("No recognized languages.")

    print()
    print("Description")
    print("────────────────────────────────")
    print(repo_info.description or "No description found.")

@app.command()
def index(repo_path: Path):
    reader = RepositoryReader(repo_path)
    files, directories_count = reader.discover_files()
    parsing_service = ParsingService()
    index_store = IndexStore(repo_path)
    indexing_service = IndexingService(parsing_service, index_store)

def main():
    app()


if __name__ == "__main__":
    main()