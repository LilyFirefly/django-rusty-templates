use std::borrow::Cow;
use std::fmt;

use divan::black_box;
use django_rusty_templates::render::filters::slugify;

fn main() {
    divan::main();
}

struct BenchCase {
    name: &'static str,
    input: &'static str,
}
impl fmt::Display for BenchCase {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}
#[divan::bench(args = [
    BenchCase { name: "Simple ASCII", input: "Hello World" },
    BenchCase { name: "With Numbers", input: "Test123 Example456" },
    BenchCase { name: "Mixed Case", input: "ThIs Is A TeSt" },
    BenchCase { name: "With Punctuation", input: "Hello, World! How are you?" },
    BenchCase { name: "Multiple Spaces", input: "Hello    World    Test" },
    BenchCase { name: "With Hyphens", input: "Hello-World-Test" },
    BenchCase { name: "Unicode Accents", input: "Héllo Wörld Tëst" },
    BenchCase { name: "Long Text", input: "This is a much longer text that contains multiple words and should test the performance with larger inputs" },
    BenchCase { name: "Special Chars", input: "Test@#$%^&*()_+={}[]|\\:;\"'<>,.?/" },
    BenchCase { name: "Mixed Unicode", input: "Café résumé naïve" },
])]
fn bench_slugify(bencher: divan::Bencher, case: &BenchCase) {
    bencher.bench_local(|| slugify(black_box(Cow::Borrowed(case.input))));
}
