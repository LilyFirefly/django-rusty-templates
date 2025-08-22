python-coverage:
    maturin develop
    pytest --cov

rust-coverage:
    #!/usr/bin/bash
    cargo llvm-cov clean --workspace
    source <(cargo llvm-cov show-env --export-prefix)
    cargo llvm-cov --no-report
    maturin develop
    pytest
    cargo llvm-cov report

rust-coverage-browser:
    #!/usr/bin/bash
    cargo llvm-cov clean --workspace
    source <(cargo llvm-cov show-env --export-prefix)
    cargo llvm-cov --no-report
    maturin develop
    pytest
    cargo llvm-cov report --open
