use divan::{Bencher, black_box};
use dtl_lexer::core::Lexer;

fn main() {
    divan::main();
}

fn lex(bencher: Bencher, unit: &str, repeats: usize) {
    let template = unit.repeat(repeats);
    bencher.bench_local(|| Lexer::new(black_box(template.as_str()).into()).count());
}

// Sizes come in pairs 4x apart so superlinear growth shows up in the report,
// and stay small enough for CodSpeed's simulation mode.

#[divan::bench(args = [250, 1000])]
fn mixed(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}{{ item.name }}{# note #}\n", lines);
}

#[divan::bench(args = [250, 1000])]
fn variables(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>{{ item.name }}</li>\n", lines);
}

#[divan::bench(args = [250, 1000])]
fn block_tags(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}<li>item</li>{% endif %}\n", lines);
}

#[divan::bench(args = [500, 2000])]
fn unclosed(bencher: Bencher, openers: usize) {
    lex(bencher, "{{ a ", openers);
}

#[divan::bench(args = [250, 1000])]
fn plain_text(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>item name</li>\n", lines);
}
