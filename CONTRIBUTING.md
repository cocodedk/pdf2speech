# Contributing to pdf2speech

## Local Setup

```sh
git clone git@github.com:cocodedk/pdf2speech.git
cd pdf2speech
python3 -m venv .venv
```

Install the CPU build of torch **before** the rest of the requirements, or
pip will pull the huge CUDA build:

```sh
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
```

Right after cloning, install the git hooks:

```sh
./scripts/install-hooks.sh
```

## Build & Test

```sh
.venv/bin/pytest -q
.venv/bin/ruff check .
```

## Local Git Setup

```sh
git config pull.rebase true
git config core.autocrlf input
git config push.autoSetupRemote true
git config init.defaultBranch main
```

## Branch Naming

Branches are kebab-case and map to a Conventional Commits type. Never
commit directly to `main`.

| Branch prefix | Commit type |
| -------------- | ----------- |
| `feature/…`    | `feat:`     |
| `fix/…`        | `fix:`      |
| `chore/…`      | `chore:`    |
| `docs/…`       | `docs:`     |
| `refactor/…`   | `refactor:` |
| `ci/…`         | `ci:`       |

Example: `feature/multi-column-pdf` → commits prefixed `feat:`.

## Commit Messages

This repo follows [Conventional Commits](https://www.conventionalcommits.org/).
The format is enforced by the `commit-msg` hook installed via
`./scripts/install-hooks.sh`, so a non-conforming commit message is
rejected locally before it ever reaches CI.

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] `.venv/bin/pytest -q` passes
- [ ] The change has been manually exercised (run the affected tool against
      a real PDF/Markdown file, not just the test suite)
- [ ] Docs (`README.md`, `CLAUDE.md`) are updated if behavior or flags changed

## A Note on Hooks

`core.hooksPath` is configured per-clone, not committed to the repo. Every
fresh clone must run `./scripts/install-hooks.sh` once before its first
commit, or the Conventional Commits check will not run locally.
