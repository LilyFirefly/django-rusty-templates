"""Run Django's template test suite against django-rusty-templates."""

import argparse
import os
import pathlib
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DJANGO_REPO_CACHE = SCRIPT_DIR / ".django"
PATCH_FILE = SCRIPT_DIR / "django_tests_use_rusty_templates.patch"


def log(header: str):
    print(f"\033[1;32m==> {header}\033[0m\n", flush=True)


def patch_django_test_suite():
    # Check if patch is already applied
    result = subprocess.run(
        ["git", "apply", "--check", "--quiet", str(PATCH_FILE)],
        cwd=DJANGO_REPO_CACHE,
        capture_output=True,
    )
    if result.returncode == 0:
        log("Applying patches to Django repository...")
        subprocess.run(
            ["git", "apply", str(PATCH_FILE)],
            cwd=DJANGO_REPO_CACHE,
            check=True,
        )
    else:
        log("Patches already applied or not applicable.")


def parse_test_output(output: str) -> str:
    """Keep individual test outcome lines and normalize them."""
    lines = []
    for line in output.splitlines():
        line = line.strip()
        if line.endswith(("ERROR", "FAIL", "ok")):
            line = re.sub(r"<lambda> at 0x.*>", "<lambda> at ..>", line)
            lines.append(line.strip())

    return "\n".join(sorted(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Run Django's template test suite against django-rusty-templates"
    )
    parser.add_argument(
        "--parsed-output",
        type=pathlib.Path,
        help="The file to write parsed output to",
    )
    args = parser.parse_args()
    if not DJANGO_REPO_CACHE.exists():
        log(f"Cloning Django repository at {DJANGO_REPO_CACHE}...")
        subprocess.run(
            [
                "git",
                "clone",
                "--config",
                "advice.detachedHead=false",
                "--quiet",
                "--depth",
                "1",
                "--no-tags",
                "https://github.com/django/django.git",
                str(DJANGO_REPO_CACHE),
            ],
            check=True,
            cwd=SCRIPT_DIR,
        )
    else:
        log(f"Using existing Django repository at {DJANGO_REPO_CACHE}")

    patch_django_test_suite()

    log("Running Django's template test suite...")

    result = subprocess.run(
        [
            "python",
            "runtests.py",
            "--parallel=1",
            "-v=2",
            "template_tests",
            "template_loader",
        ],
        cwd=DJANGO_REPO_CACHE / "tests",
        # Ensure the cloned Django repo takes precedence over installed Django
        env={**os.environ, "PYTHONPATH": str(DJANGO_REPO_CACHE)},
        capture_output=bool(args.parsed_output),
        text=True,
    )
    print(result.stderr, end="", file=sys.stderr)

    if args.parsed_output:
        parsed = parse_test_output(result.stderr)
        with open(args.parsed_output, "w") as f:
            f.write(parsed)
            f.write("\n")
        log(f"Parsed output written to {args.parsed_output}")

    log("Done !")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
