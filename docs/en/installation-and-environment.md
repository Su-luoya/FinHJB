# Installation and Environment

Read this page before your first solve.

This page separates two goals that used to get mixed together:

- installing the published `finhjb` package from PyPI,
- reproducing the repository BCW examples and building docs from source.

## Goal

By the end of this page, you should be able to:

- install the published package when you only need the library API,
- set up a repository environment when you want the BCW scripts or local docs,
- avoid the most common JAX and Matplotlib environment issues,
- run a minimal verification command before moving to the BCW tutorials.

If you already know the environment is healthy, move to [Getting Started](./getting-started.md). If installation fails, keep this page open and pair it with [Troubleshooting](./troubleshooting.md).

## Recommended Baseline

FinHJB is currently easiest to use in the following setup:

| Item | Recommendation |
|---|---|
| Python | `>=3.10` |
| Package manager | `uv` or `pip` |
| First backend target | CPU |
| Plotting on remote machines | `MPLBACKEND=Agg` |
| Docs build from source | `uv sync --group docs` |

For a first successful run, do not start by optimizing for GPU, notebook integration, or custom plotting backends. Start with the simplest reproducible environment.

## Step 1: Choose Your Path

Use the path that matches what you actually want to do.

### Path A: Use FinHJB as a package

This is the right path if you want to import `finhjb` in your own project and do not need the repository example scripts.

Install with one of these commands:

```bash
uv add finhjb
```

```bash
pip install finhjb
```

Then run a minimal import check:

```bash
python -c "import finhjb as fjb; print('exports:', len(fjb.__all__), 'first:', fjb.__all__[:5])"
```

Important limitation:

- the published wheel contains the `finhjb` package,
- it does not contain `src/example/BCW2011Liquidation.py`,
- it does not contain `src/example/BCW2011Hedging.py`,
- it does not contain the repository docs tree.

So if your goal is to reproduce the BCW walkthroughs line by line, continue with Path B instead.

### Path B: Work from repository source

Use this path if you want to:

- run `src/example/BCW2011Liquidation.py`,
- run `src/example/BCW2011Hedging.py`,
- build the local Sphinx docs,
- or work on the package itself.

## Step 2: Clone the Repository

```bash
git clone https://github.com/Su-luoya/FinHJB.git
cd FinHJB
```

You should run the rest of the commands from the repository root.

## Step 3: Install Repository Dependencies

The installation section above covered package installation. The commands below are specifically for the repository checkout.

```bash
uv sync
```

If you also want to build the Sphinx docs locally:

```bash
uv sync --group docs
```

The project documentation and CI use `uv`, so if you hit an environment mismatch, prefer returning to `uv sync`.

## Step 4: Verify the Repository Python Environment

Run a very small import test before attempting a full solve:

```bash
uv run python -c "import finhjb as fjb; print('exports:', len(fjb.__all__), 'first:', fjb.__all__[:5])"
```

You should see a short list containing names such as `Config`, `AbstractBoundary`, and `Solver`.

Next, verify that the example modules import:

```bash
uv run python -c "from src.example.BCW2011Liquidation import Parameter; print(Parameter())"
uv run python -c "from src.example.BCW2011Hedging import Parameter; print(Parameter())"
```

If these imports fail, do not proceed to the walkthrough pages yet. Fix the environment first.

## Step 5: Configure Plotting For Your Machine

The BCW example scripts import Matplotlib. On laptops with a desktop session, that is usually fine. On servers, CI, and remote shells, set:

```bash
export MPLBACKEND=Agg
```

Then run the example commands with that environment:

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

This changes only plotting behavior. It does not change the economics or solver output.

### Windows note

If you are not in a POSIX-like shell, the environment-variable syntax differs. The important part is that Matplotlib uses the `Agg` backend before the script imports `matplotlib.pyplot`.

## Step 6: Run a Minimal Sanity Check

Before solving BCW, run one command that exercises the package in the project environment:

```bash
uv run python - <<'PY'
import finhjb as fjb
print("versioned exports:", fjb.__all__)
print("Config example:", fjb.Config())
PY
```

This is a good environment checkpoint. If it fails, your first task is still installation, not numerical debugging.

## Step 7: Optional But Useful Checks

### Build the documentation locally

```bash
uv run sphinx-build -b dirhtml docs build/sphinx/dirhtml -c .sphinx -W --keep-going
```

This confirms:

- the docs dependency group is installed,
- MyST + autodoc are working,
- imports succeed in the docs build context.

### Run the doc contract tests

```bash
uv run pytest -q tests/test_doc_and_api_contracts.py
```

That test file checks bilingual page coverage and basic documentation/API expectations.

## Platform Notes

### macOS

For package usage, the smoothest route is usually:

```bash
python -c "import finhjb"
```

If you are working from repository source rather than a plain package install, use `uv sync` first and then `uv run python -c "import finhjb"`.

On Apple Silicon, avoid changing anything until the default CPU setup works.

### Linux / remote servers

Most failures are plotting-related rather than JAX-related. Set:

```bash
export MPLBACKEND=Agg
```

and keep your first run non-interactive.

### Windows

The project itself is Python-based, but many examples in the docs use Unix-style shell snippets. If quoting or environment-variable syntax becomes awkward, use PowerShell equivalents or WSL.

## What "Installed Correctly" Means

A healthy package-only environment is one where:

1. `python -c "import finhjb"` succeeds.

A healthy repository environment for BCW reproduction is one where all of the following are true:

1. `uv run python -c "import finhjb"` succeeds.
2. `uv run python -c "from src.example.BCW2011Liquidation import Parameter"` succeeds.
3. `uv run sphinx-build ...` succeeds if you installed the docs group.
4. You can run the BCW liquidation example without import errors or plotting-backend errors.

If only the package import works but the example script fails, the setup is not complete yet for repository walkthroughs.

## Common Installation Failure Patterns

| Symptom | Likely cause | First fix to try |
|---|---|---|
| `ModuleNotFoundError: No module named 'finhjb'` | you are using the wrong environment | rerun in the environment where you installed the package |
| `ModuleNotFoundError: No module named 'jax'` | dependencies were not installed in the active repository environment | run `uv sync` again |
| Matplotlib GUI or display error | remote/headless machine | set `MPLBACKEND=Agg` |
| Sphinx command fails on missing package | docs dependencies not installed | run `uv sync --group docs` |
| Example imports fail from repo root | wrong working directory or missing repository checkout | `cd` into repository root and retry |

## After Installation: The First Real Page To Read

Once the environment is healthy, go directly to [Getting Started](./getting-started.md). That page is designed to answer the next practical question:

"Can I run BCW and tell whether the result is correct?"
