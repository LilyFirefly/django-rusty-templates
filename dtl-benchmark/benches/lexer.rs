use divan::{Bencher, black_box};
use dtl_lexer::core::Lexer;

fn main() {
    divan::main();
}

fn lex(bencher: Bencher, unit: &str, repeats: usize) {
    let template = unit.repeat(repeats);
    bencher.bench_local(|| Lexer::new(black_box(template.as_str()).into()).count());
}

// Real page, mostly text.
#[divan::bench]
fn django_asv_base(bencher: Bencher) {
    lex(bencher, include_str!("django-asv/base.html"), 1);
}

// Real page, mostly tags.
#[divan::bench]
fn django_asv_permalink(bencher: Bencher) {
    lex(bencher, include_str!("django-asv/permalink.html"), 1);
}

// Tags, variables and comments back to back.
#[divan::bench(args = [250, 1000])]
fn mixed(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}{{ item.name }}{# note #}\n", lines);
}

// Variables between text.
#[divan::bench(args = [250, 1000])]
fn variables(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>{{ item.name }}</li>\n", lines);
}

// Tags between text.
#[divan::bench(args = [250, 1000])]
fn block_tags(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}<li>item</li>{% endif %}\n", lines);
}

// Unclosed variables on a single line.
#[divan::bench(args = [500, 2000])]
fn unclosed(bencher: Bencher, openers: usize) {
    lex(bencher, "{{ a ", openers);
}

// Text only.
#[divan::bench(args = [250, 1000])]
fn plain_text(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>item name</li>\n", lines);
}
