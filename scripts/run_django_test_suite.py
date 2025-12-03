"""Run Django's template test suite against django-rusty-templates."""

import argparse
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DJANGO_REPO_CACHE = SCRIPT_DIR / ".django"
PATCH_FILE = SCRIPT_DIR / "django_tests_use_rusty_templates.patch"

# These are skipped because they are flaky when ran with django-rusty-templates
_SKIPPED_TESTS = (
    "test_simple_block_tag_missing_content",
    "test_simple_block_tag_missing_context",
    "test_simple_block_tag_missing_context_no_params",
    "test_simple_block_tag_with_context_missing_content",
    "test_simple_block_tag_errors",
    "test_simple_tag_missing_context",
    "test_simple_tag_missing_context_no_params",
    "test_simple_tag_errors",
    "test_simpletag_renamed03",
)


def log(header: str):
    print(f"\033[1;32m==> {header}\033[0m\n", flush=True)


def patch_django_test_suite():
    # Check if patch is already applied
    result = subprocess.run(
        ["git", "apply", "--check", str(PATCH_FILE)],
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


def _format_summary(summary: Counter[str]) -> str:
    return " / ".join([f"{count} {test}" for test, count in sorted(summary.items())])


def _format_passing_test_pct(summary: Counter[str]) -> str:
    return f"Django test suite passing: {summary.get('OK', 0) / summary.total() * 100:.2f}%"


def parse_test_output(output: str) -> tuple[Counter[str], str]:
    """Keep individual test outcome lines and normalize them."""
    lines = []
    summary = Counter()
    for line in output.splitlines():
        line = line.strip()
        if line.startswith(_SKIPPED_TESTS):
            continue
        if line.endswith(("ERROR", "FAIL", "ok")):
            print(line)
            line = re.sub(r"<lambda> at 0x.*>", "<lambda> at ..>", line)
            try:
                status = line.split("... ", maxsplit=1)[1]
            except IndexError:
                print(line)
                raise

            summary[status.upper()] += 1
            lines.append(line.strip())

    return summary, "\n".join(
        [_format_passing_test_pct(summary), _format_summary(summary), *sorted(lines)]
    ) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Run Django's template test suite against django-rusty-templates"
    )
    parser.add_argument(
        "--parsed-output",
        type=Path,
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

    summary, formatted_test_output = parse_test_output(result.stderr)
    log(_format_passing_test_pct(summary))
    log(_format_summary(summary))

    if args.parsed_output:
        Path(args.parsed_output).write_text(formatted_test_output)
        log(f"Parsed output written to {args.parsed_output}")

    log("Done !")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
