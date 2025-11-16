//! Slugify Benchmark
//!
//! Run with: `cargo bench --bench slugify_bench`
//!
//! ## Latest Results (AMD Ryzen 9 7950X)
//! The new version is 1.9x to 5.1x faster than the regex-based implementation
//!
//! | Test Case         | Old (regex) | New (char-iterator) | Speedup  |
//! |-------------------|-------------|---------------------|----------|
//! | Simple ASCII      | 211.09 ns   | 77.85 ns            | 2.71x    |
//! | With Numbers      | 274.38 ns   | 119.71 ns           | 2.29x    |
//! | Mixed Case        | 271.69 ns   | 95.61 ns            | 2.84x    |
//! | With Punctuation  | 469.55 ns   | 166.36 ns           | 2.82x    |
//! | Multiple Spaces   | 328.72 ns   | 140.45 ns           | 2.34x    |
//! | With Hyphens      | 263.26 ns   | 107.48 ns           | 2.45x    |
//! | Unicode Accents   | 291.46 ns   | 130.20 ns           | 2.24x    |
//! | Long Text         | 1,271.2 ns  | 660.34 ns           | 1.93x    |
//! | Special Chars     | 946.20 ns   | 185.09 ns           | 5.11x    |
//! | Mixed Unicode     | 340.86 ns   | 141.90 ns           | 2.40x    |

use criterion::{Criterion, criterion_group, criterion_main};
use django_rusty_templates::render::filters::slugify;
use regex::Regex;
use std::borrow::Cow;
use std::hint::black_box;
use std::sync::LazyLock;
use unicode_normalization::UnicodeNormalization;

// Old regex-based implementation
static NON_WORD_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[^\w\s-]").expect("Static string will never panic"));

static WHITESPACE_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[-\s]+").expect("Static string will never panic"));

fn slugify_old(content: Cow<str>) -> Cow<str> {
    let content = content
        .nfkd()
        // first decomposing characters, then only keeping
        // the ascii ones, filtering out diacritics for example.
        .filter(|c| c.is_ascii())
        .collect::<String>()
        .to_lowercase();
    let content = NON_WORD_RE.replace_all(&content, "");
    let content = content.trim();
    let content = WHITESPACE_RE.replace_all(content, "-");
    Cow::Owned(content.to_string())
}

fn benchmark_slugify(c: &mut Criterion) {
    let test_cases = vec![
        ("Simple ASCII", "Hello World"),
        ("With Numbers", "Test123 Example456"),
        ("Mixed Case", "ThIs Is A TeSt"),
        ("With Punctuation", "Hello, World! How are you?"),
        ("Multiple Spaces", "Hello    World    Test"),
        ("With Hyphens", "Hello-World-Test"),
        ("Unicode Accents", "Héllo Wörld Tëst"),
        (
            "Long Text",
            "This is a much longer text that contains multiple words and should test the performance with larger inputs",
        ),
        ("Special Chars", "Test@#$%^&*()_+={}[]|\\:;\"'<>,.?/"),
        ("Mixed Unicode", "Café résumé naïve"),
    ];

    let mut group = c.benchmark_group("slugify");

    for (name, input) in test_cases.iter() {
        group.bench_function(format!("old/{}", name), |b| {
            b.iter(|| slugify_old(black_box(Cow::Borrowed(input))))
        });

        group.bench_function(format!("new/{}", name), |b| {
            b.iter(|| slugify(black_box(Cow::Borrowed(input))))
        });
    }

    group.finish();
}

criterion_group!(benches, benchmark_slugify);
criterion_main!(benches);
