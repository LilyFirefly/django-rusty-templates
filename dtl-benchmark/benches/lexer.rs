use divan::{Bencher, black_box};
use djangofmt_corpus::{ALL_TEMPLATES, Syntax, Template};
use dtl_lexer::core::Lexer;

fn main() {
    divan::main();
}

fn lex(bencher: Bencher, unit: &str, repeats: usize) {
    let template = unit.repeat(repeats);
    bencher.bench_local(|| Lexer::new(black_box(template.as_str()).into()).count());
}

// Corpus: djangofmt's benchmark pages, from mostly text to mostly tags.
#[divan::bench(args = ALL_TEMPLATES.into_iter().filter(|t| t.syntax == Syntax::Django))]
fn corpus(bencher: Bencher, template: &'static Template) {
    lex(bencher, template.code, 1);
}

// Synthetic: tags, variables and comments back to back.
#[divan::bench(args = [250, 1000])]
fn mixed(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}{{ item.name }}{# note #}\n", lines);
}

// Synthetic: variables between text.
#[divan::bench(args = [250, 1000])]
fn variables(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>{{ item.name }}</li>\n", lines);
}

// Synthetic: tags between text.
#[divan::bench(args = [250, 1000])]
fn block_tags(bencher: Bencher, lines: usize) {
    lex(bencher, "{% if item %}<li>item</li>{% endif %}\n", lines);
}

// Synthetic: unclosed variables on a single line.
#[divan::bench(args = [500, 2000])]
fn unclosed(bencher: Bencher, openers: usize) {
    lex(bencher, "{{ a ", openers);
}

// Synthetic: text only.
#[divan::bench(args = [250, 1000])]
fn plain_text(bencher: Bencher, lines: usize) {
    lex(bencher, "<li>item name</li>\n", lines);
}
