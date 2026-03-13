## Getting started with development

django-rusty-templates is written in Rust, so you'll need to install the
[Rust toolchain](https://www.rust-lang.org/tools/install).

### Option 1: Using uv

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver. Using it will significantly speed up dependency installation.

First, install uv:

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then sync the dependencies and activate the automatically created virtual env:

```bash
$ uv sync
$ source .venv/bin/activate
```

### Option 2: Using standard Python tools

If you prefer not to use uv, you can set up your development environment with standard Python tools:

```bash
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install --group dev
```

Note: The `[dev]` dependency group is defined in `pyproject.toml` and includes all necessary development dependencies.

## Running tests

To run the Python tests, build Django Rusty Templates in develop mode with maturin and then run pytest.
Each change in rust needs a new execution of maturin develop.

```bash
$ maturin develop
$ pytest
```

You can also run the Rust tests:

```bash
$ cargo test --workspace
```

If you get an `ImportError` from python, you may need to set the `PYTHONPATH` environment variable:

```bash
export PYTHONPATH=/path/to/venv/lib/python3.x/site-packages
```

## Pre-commit hooks

You can optionally install [pre-commit](https://pre-commit.com/#installation) hooks to automatically run some validation checks when making a commit:

```shell
$ pip install pre-commit  # or: uv tool install pre-commit
$ pre-commit install
```

## Coverage

When submitting a PR we check coverage. You can check coverage locally by running a command from the `justfile`:

```bash
$ just python-coverage
$ just rust-coverage
$ just rust-coverage-browser
```

You will need [Just](https://github.com/casey/just) installed.
