set shell := ["bash", "-euox", "pipefail", "-c"]

# List available recipes
_default:
    @just --list --unsorted

# Bootstrap the environment for running the test suite
bootstrap:
    #!/usr/bin/env bash
    set -euox pipefail
    # Compile translations
    cd tests && django-admin compilemessages

# Build the Rust extension and run the Python test suite (extra args forwarded to pytest)
[group('test')]
python-test *ARGS:
    maturin develop
    pytest {{ARGS}}

# Run the Python test suite under coverage
[group('coverage')]
python-coverage:
    maturin develop
    pytest --cov

# Print a terminal Rust coverage report from the Python test suite
[group('coverage')]
rust-coverage:
    #!/usr/bin/env bash
    set -euox pipefail
    cargo llvm-cov clean --workspace
    source <(cargo llvm-cov show-env --sh)
    cargo llvm-cov --no-report
    maturin develop
    pytest
    cargo llvm-cov report --workspace

# Generate an HTML Rust coverage report and open it in the browser
[group('coverage')]
rust-coverage-browser:
    #!/usr/bin/env bash
    set -euox pipefail
    cargo llvm-cov clean --workspace
    source <(cargo llvm-cov show-env --sh)
    cargo llvm-cov --no-report
    maturin develop
    pytest
    cargo llvm-cov report --workspace --open
