# Repo Assist

AI model agnostic assistant for understanding and working with unfamiliar Git repositories.

## Current Status

Work in progress.

The current version provides basic repository inspection, including:

- Git repository and branch information
- File and directory statistics
- Line counts
- Basic programming language detection
- CLI interface

The current CLI can inspect a repository with:
```bash
uv run repo-assist <path_of_repo>   
```
after installing the dependencies with `uv`.