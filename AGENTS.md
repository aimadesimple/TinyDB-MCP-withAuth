# Repository Guidelines

## Project Structure & Module Organization

- `tinydb_remote_server.py` is the application entry point. It configures the
  FastMCP HTTP server and exposes the `insert_data`, `get_all_data`, and
`delete_all_data` tools.
- `pyproject.toml` defines the Python project and runtime dependencies.
- `NOTES.md` contains the project walkthrough, deployment notes, and usage
  examples. Keep it aligned with changes to the server workflow.
- Runtime data is written to `db.json`; treat it as local, ephemeral data and
  do not commit it.

Place future tests in `tests/`; introduce a package only when the application
outgrows a single module.

## Build, Test, and Development Commands

Use `uv` to manage Python and dependencies:

```bash
uv sync                              # install the project dependencies
uv run python tinydb_remote_server.py # run the MCP HTTP server locally
uv run --frozen python tinydb_remote_server.py # run with the lockfile in CI
```

The server uses `PORT`, defaulting to `10000`. Connect MCP Inspector to
`http://localhost:10000/mcp` for local verification.

## Coding Style & Naming Conventions

Use Python 3.13+ and four-space indentation. Follow standard Python naming:
`snake_case` for functions and variables, `PascalCase` for classes, and clear
verb-led names for MCP tools such as `insert_data`. Keep imports grouped at the
top, add type annotations to public tool parameters and return values, and use
concise docstrings that describe inputs, outputs, and examples where useful.

No formatter, linter, or automated test framework is configured.

## Testing Guidelines

There is currently no automated test suite. For behavior changes, manually
exercise each affected MCP tool with representative non-sensitive data. Add
tests as `tests/test_<feature>.py` when introducing coverage.

## Commit & Pull Request Guidelines

This workspace has no Git history yet; use short, imperative, focused commit
subjects, for example `Add input validation to insert_data`. Before committing,
run `git diff --cached --check` and exclude `.venv/`, `db.json`, secrets, and
other generated files. Pull requests should summarize the behavior change,
list validation performed, link related issues when applicable, and include
request/response examples for changes to MCP tools.

## Security & Configuration

Load local configuration from environment variables; never hard-code secrets.
This server is intended for demonstration and TinyDB storage may be ephemeral
on hosted services. Do not use it for sensitive or durable production data
without adding authentication and persistent storage.
