# Installation and Environment

Read this page before your first solve.

The goal is not only "the package installs," but "you can run the BCW examples in the same environment that you will later use for your own model."

## Goal

By the end of this page, you should be able to:

- create a working local environment,
- import `finhjb` from the repository checkout,
- avoid the most common JAX and Matplotlib environment issues,
- run a minimal verification command before moving to the BCW tutorials.

If you already know the environment is healthy, move to [Getting Started](./getting-started.md). If installation fails, keep this page open and pair it with [Troubleshooting](./troubleshooting.md).

## Recommended Baseline

FinHJB is currently easiest to use in the following setup:

| Item | Recommendation |
|---|---|
| Python | `>=3.10` |
| Environment manager | `uv` |
| First backend target | CPU |
| Plotting on remote machines | `MPLBACKEND=Agg` |
| Docs build | `uv sync --group docs` |

For a first successful run, do not start by optimizing for GPU, notebook integration, or custom plotting backends. Start with the simplest reproducible environment.

## Step 1: Clone the Repository

```bash
git clone https://github.com/Su-luoya/FinHJB.git
cd FinHJB
```

You should run the rest of the commands from the repository root.

## Step 2: Install Dependencies

### Recommended: `uv`

```bash
uv sync
```

If you also want to build the Sphinx docs locally:

```bash
uv sync --group docs
```

### Alternative: editable `pip`

```bash
pip install -e .
```

The project documentation and CI use `uv`, so if you hit an environment mismatch, prefer returning to `uv sync`.

## Step 3: Verify the Python Environment

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

## Step 4: Configure Plotting For Your Machine

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

## Step 5: Run a Minimal Sanity Check

Before solving BCW, run one command that exercises the package in the project environment:

```bash
uv run python - <<'PY'
import finhjb as fjb
print("versioned exports:", fjb.__all__)
print("Config example:", fjb.Config())
PY
```

This is a good "environment checkpoint." If it fails, your first task is still installation, not numerical debugging.

## Step 6: Optional But Useful Checks

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

Usually the smoothest route is simply:

```bash
uv sync
uv run python -c "import finhjb"
```

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

A healthy environment is one where all of the following are true:

1. `uv run python -c "import finhjb"` succeeds.
2. `uv run python -c "from src.example.BCW2011Liquidation import Parameter"` succeeds.
3. `uv run sphinx-build ...` succeeds if you installed the docs group.
4. You can run the BCW liquidation example without import errors or plotting-backend errors.

If only the package import works but the example script fails, the setup is not complete yet.

## Common Installation Failure Patterns

| Symptom | Likely cause | First fix to try |
|---|---|---|
| `ModuleNotFoundError: No module named 'finhjb'` | you are using system Python instead of project environment | rerun via `uv run ...` |
| `ModuleNotFoundError: No module named 'jax'` | dependencies were not installed in the active environment | run `uv sync` again |
| Matplotlib GUI or display error | remote/headless machine | set `MPLBACKEND=Agg` |
| Sphinx command fails on missing package | docs dependencies not installed | run `uv sync --group docs` |
| Example imports fail from repo root | wrong working directory | `cd` into repository root |

## After Installation: The First Real Page To Read

Once the environment is healthy, go directly to [Getting Started](./getting-started.md). That page is designed to answer the next practical question:

"Can I run BCW and tell whether the result is correct?"

