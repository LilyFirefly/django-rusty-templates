use divan::{Bencher, black_box};
use djangofmt_corpus::{ALL_TEMPLATES, Syntax, Template};
use dtl_lexer::core::Lexer;

fn main() {
    divan::main();
}

fn lex(bencher: Bencher, template: &str) {
    bencher.bench_local(|| Lexer::new(black_box(template).into()).count());
}

// djangofmt's benchmark pages, from mostly text to mostly tags.
#[divan::bench(args = ALL_TEMPLATES.into_iter().filter(|t| t.syntax == Syntax::Django))]
fn corpus(bencher: Bencher, template: &'static Template) {
    lex(bencher, template.code);
}

// Repeated units at two sizes, to expose non-linear scaling.
#[divan::bench(args = synthetic_templates())]
fn synthetic(bencher: Bencher, template: &Template) {
    lex(bencher, template.code);
}

fn synthetic_templates() -> impl Iterator<Item = Template> {
    [
        // Tags, variables and comments back to back.
        (
            "mixed",
            "{% if item %}{{ item.name }}{# note #}\n",
            [250, 1000],
        ),
        // Variables between text.
        ("variables", "<li>{{ item.name }}</li>\n", [250, 1000]),
        // Tags between text.
        (
            "block_tags",
            "{% if item %}<li>item</li>{% endif %}\n",
            [250, 1000],
        ),
        // Unclosed variables on a single line.
        ("unclosed", "{{ a ", [500, 2000]),
        // Text only.
        ("plain_text", "<li>item name</li>\n", [250, 1000]),
    ]
    .into_iter()
    .flat_map(|(name, unit, repeats)| {
        // Leaked to fit `Template`, which gives the same label as the corpus.
        repeats.map(|n| Template {
            name,
            code: unit.repeat(n).leak(),
            syntax: Syntax::Django,
        })
    })
}
