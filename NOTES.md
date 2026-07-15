---
name: notes-creating-tinydb-remote-mcp-withAuth
description: Notes on creating a TinyDB Remote MCP server
author: Saurabh Lal
---

This `NOTES.md` file contains rough notes on this project. Other documents like `SETUP.md`, `GUIDE.md`, and `README.md` files can be created with the help of `NOTES.md`.


# Steps to create the TinyDB Remote MCP server with Auth

## Step 1: Initialise the Project

Initialise the project using uv as package manager

```bash
uv init --bare
```

Use `--bare` to create the smallest possible project, avoiding extra starter files like source code or a README. We do not use `--script` because it manages dependencies within a single Python file and uses a cached virtual environment instead of creating a project-specific virtual environment with `pyproject.toml` and `uv.lock`. The `--bare` flag gives us a minimal project while still benefiting from `uv`'s dependency management and local virtual environment.

## Step 2: Add dependencies

Add the dependencies

```bash
uv add mcp tinydb python-dotenv
```

`uv` will automatically create a virtual environment for you when you run `uv add`.

Sometime you might have to activate the virtual environment using `venv source/bin/activate`

In the IDE, you might have to select the environment manually.

If I have to add dependencies later then use `uv sync`

## Step 3: Create the `server.py` file

Create the main MCP server file <file_name.py> tinydb_remote_server.py

```bash
touch tinydb_remote_server.py
```

## Step 4: Add the MCP boilerplate code

```python
# MCP Boilerplate Code
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# For Local MCP using stdio
# mcp = FastMCP("tinydb-mcp")

# For Remote MCP hosted on a platform
mcp = FastMCP(
    "tinydb-remote-mcp",
    host="0.0.0.0",
    port=int(os.environ.get("PORT","10000")),
)

@mcp.tool()
def say_hello(name:str) -> str:
    """
    A simple MCP tool to print 'Hello <name>!', consistent greeting.

    Args:
        name(str): Name of the user.

    Returns:
        str: The string "Hello <name>!"
    """
    return f'Hello {name}!'

if __name__ == "__main__":
    # For local MCP with transport stdio
    # mcp.run(transport="stdio")
    # For remote MCP hosted on a platform
    mcp.run(transport="streamable-http")
```

For a remote MCP server, its HTTP process must bind to a network interface and
port that the hosting platform can reach. `0.0.0.0` accepts external traffic.
Using the `PORT` environment variable is not required for every deployment,
but is the common convention for managed web hosts; each host supplies or
documents its own port. The `10000` value is only a local fallback.

## Step 5: Add the tools, resources and prompts to the MCP

In this step you add the tools, resources and prompts required to accomplish the goal.

## Step 6: Add Authentication

This project uses Auth0 as an OAuth 2.1 authorization server. Auth0 handles
email/password and Google sign-in; this MCP validates the access token that an
MCP client sends with every request. All authenticated users currently need the
single `tinydb:tools` permission and can use all three TinyDB tools.

Follow Auth0's [Authorization for Your MCP Server](https://auth0.com/ai/docs/mcp/get-started/authorization-for-your-mcp-server)
quickstart to configure the tenant. In Auth0, enable **Resource Parameter
Compatibility Profile**, **Include Issuer in Authorization Responses**, and
**Dynamic Client Registration**. Create an API with this identifier:

```text
https://tinydb-mcp-withauth.onrender.com/mcp
```

Use the `RS256` signing algorithm, the `rfc9068_profile_authz` token dialect,
and add the `tinydb:tools` permission. Before enabling Dynamic Client
Registration for MCP Inspector and ChatGPT, grant `tinydb:tools` as a default
permission for third-party applications. Promote the Auth0 database and Google
connections to domain-level connections so external MCP clients can offer both
sign-in methods.

Copy `.env.example` to `.env` for local development and set `AUTH0_DOMAIN` to
your tenant domain. On Render, set `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`,
`MCP_SERVER_URL`, and `AUTH0_REQUIRED_SCOPE` as environment variables. Do not
commit `.env`, `db.json`, Google credentials, or Auth0 secrets.

After deployment, check that unauthenticated requests return `401` with a
`WWW-Authenticate` header. Then connect with MCP Inspector or ChatGPT, sign in
through Auth0, and exercise all three tools with test data.

## Step 7: Publish the Repository to GitHub

Use Git to initialize and commit the project, then use the GitHub CLI (`gh`)
to authenticate, create the public repository, push the initial commit, and
verify the result. Run these commands from the project root.

```bash
# Initialize the local repository and create the initial commit
git init -b main
git add AGENTS.md NOTES.md .env.example .gitignore auth0_mcp.py pyproject.toml tinydb_remote_server.py uv.lock
git status --short
git diff --cached --check
git commit -m "Initial TinyDB MCP server"

# Authenticate GitHub CLI in a browser and confirm the active account
gh auth login --hostname github.com --web --git-protocol https
gh auth status

# Create the public repository, configure origin, and push main
gh repo create AIMadeSimple/TinyDB-MCP-withAuth --public --source=. --remote=origin --push

# Confirm the repository settings and local remote
gh repo view AIMadeSimple/TinyDB-MCP-withAuth --json nameWithOwner,visibility,defaultBranchRef,url
git remote -v
```

For later changes, stage the intended files, create a focused commit, and push
the current `main` branch to GitHub:

```bash
git add NOTES.md
git commit -m "Update NOTES.md"
git push -u origin main
```

### CLI flag reference

- `git init -b main`: `-b` sets the initial branch name to `main` instead of
  Git's configured default.
- `git status --short`: `--short` prints a compact, one-line status for each
  changed file.
- `git diff --cached --check`: `--cached` compares the staged files with the
  last commit; `--check` reports whitespace errors without changing files.
- `git commit -m "..."`: `-m` supplies the commit message directly on the
  command line.
- `git remote -v`: `-v` shows the fetch and push URLs for each remote.
- `git push -u origin main`: `-u` (also `--set-upstream`) makes
  `origin/main` the upstream for the local `main` branch, enabling later
  `git push` and `git pull` commands without specifying the remote and branch.
- `gh auth login --hostname github.com --web --git-protocol https`:
  `--hostname` chooses GitHub.com, `--web` opens browser-based authentication,
  and `--git-protocol` selects HTTPS for Git remotes.
- `gh repo create ... --public --source=. --remote=origin --push`:
  `--public` sets repository visibility, `--source=.` uses the current
  directory, `--remote=origin` names the created Git remote, and `--push`
  pushes the current branch after creating the repository.
- `gh repo view ... --json nameWithOwner,visibility,defaultBranchRef,url`:
  `--json` limits the output to the listed repository fields in JSON format.

The `gh repo create` command creates the repository under the `AIMadeSimple`
organization, configures it as the local `origin` remote, and pushes the
current `main` branch. The explicit `git add` list avoids committing local
environment files or the runtime TinyDB database.

## Step 8: Deploy the Remote MCP on Render

In the Render Dashboard, select **New > Web Service**, choose the
`AIMadeSimple/TinyDB-MCP-withAuth` repository and the `main` branch, and select the
Python runtime. Use these commands:

```bash
# Build Command
uv sync --frozen && uv cache prune --ci

# Start Command
uv run --frozen python tinydb_remote_server.py
```

Choose the Free instance type and create the service. Render provides `PORT`
(default `10000`), which the server reads automatically; do not set it
manually. `--frozen` installs/runs exactly the locked dependencies, while
`--ci` removes uv's cache after the build. Render redeploys automatically
after later pushes to `main`.

### Ignore Markdown-only changes

To avoid a deployment when a commit changes only Markdown files:

1. Open the Render service and select **Settings**.
2. Under **Build & Deploy**, find **Build Filters** and click **Edit**.
3. Add `**/*.md` as an **Ignored Path** and save the changes.

A commit that changes only `.md` files will not deploy; a commit that also
changes application files will still trigger a deployment.

TinyDB writes to `db.json` on the service filesystem. On a Free service this
data is ephemeral and can be lost after a restart or redeploy. Auth0 protects
the MCP endpoint, but all authenticated users currently share the same data;
do not store sensitive or durable production data.

## Step 9: Using MCP Inspector

After the deploy is live, start MCP Inspector locally:

```bash
npx @modelcontextprotocol/inspector
```

Open the displayed local URL, select the **Streamable HTTP** transport, and
enter the remote endpoint:

```text
https://<render-service-name>.onrender.com/mcp
```

To list the available tools without the Inspector UI, use its CLI mode:

```bash
npx @modelcontextprotocol/inspector --cli https://<render-service-name>.onrender.com/mcp --transport http --method tools/list
```

## Step 10: Connect MCP to OpenAI Web App

1. In ChatGPT, open **Settings > Security and login** and enable **Developer mode**.
2. Open **Settings > Plugins** or visit `https://chatgpt.com/plugins`.
3. Click **+** (plus) to create an app, then enter:
   - **Name:** `TinyDB MCP`
   - **Description:** `Store, retrieve, and clear TinyDB records.`
   - **MCP server URL:** `https://<your-render-service>.onrender.com/mcp`
4. Click **Create** and confirm ChatGPT shows `insert_data`, `get_all_data`, and `delete_all_data`.
5. In a separate ChatGPT project, click **+ > More**, select the app, and test inserting or retrieving data.

Use test data only: all authenticated users currently share the same TinyDB
records.

## Step 11: Create a README.md file

The README.md file should contain a basic overview of this project.

This is a simple project to help people understand how to create and use MCP servers. I didn't find a super detailed repository that walks people through how to create and connect to an MCP server hence I have created this repository.

The detailed Steps for how to create an MCP are in NOTES.md file.

What does this MCP do?

How to use the MCP?

With MCP Inspector

With OpenAI Web App

With Codex

With Claude Web App

With Claude Code

# FAQs

## When creating a Python project, should I create a virtual environment first or run `uv init` first?

Run `uv init` first for a new Python project.

Typical flow:

```bash
mkdir my-project
cd my-project
uv init
uv add requests
uv run python main.py
```

`uv init` creates the project structure and `pyproject.toml`. After that, `uv add` or `uv sync` will create and manage the virtual environment automatically, usually in `.venv`.

You only need to manually create the virtual environment first if you have a specific reason, such as pinning a Python version before initializing:

```bash
uv venv --python 3.12
uv init
uv sync
```

For most projects, prefer:

```bash
uv init
uv add <packages>
```

## What are the common `uv init` options / CLI flags and when should they be used?

These options change what kind of project `uv init` creates.

Usage: uv init [OPTIONS] [PATH]

> **Tip:** `uv init --help` is a useful command to understand which [OPTIONS] [PATH] should be used with uv init

`uv init` by default creates an application project i.e. similar to `uv init --app`.

### `--bare`

Only creates a `pyproject.toml` file.

Use this when you want the smallest possible project setup and do not want `uv` to create extra files like source files, README files, or other starter structure.

```bash
uv init --bare
```

### `--package`

Sets up the project so it can be built as a Python package.

Use this when you want your project to be installable/buildable, for example as a wheel (`.whl`) or source distribution (`.tar.gz`).

```bash
uv init --package
```

### `--no-package`

Does not set up the project to be built as a Python package.

Use this when the project is only meant to be run locally as an application or script, and you do not need packaging/build configuration.

```bash
uv init --no-package
```

### `--app`

Creates a project for an application.

Use this when you are building something meant to be run directly, such as a CLI tool, API server, MCP server, automation script, or app.

```bash
uv init --app
```

### `--lib`

Creates a project for a library.

Use this when you are building reusable Python code that other Python code will import.

```bash
uv init --lib
```

### `--script`

Creates a Python script.

Use this when you want a single-file Python script instead of a full project folder.

```bash
uv init --script example.py
```
