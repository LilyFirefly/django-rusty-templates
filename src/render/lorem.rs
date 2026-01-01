use miette::{Diagnostic, SourceSpan};
use rand::Rng;
use rand::seq::SliceRandom;
use std::borrow::Cow;
use thiserror::Error;

use dtl_lexer::tag::TagParts;
use dtl_lexer::types::{At, TemplateString};

static COMMON_P: &str = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod \
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud \
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in \
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";

static WORDS: [&str; 182] = [
    "exercitationem",
    "perferendis",
    "perspiciatis",
    "laborum",
    "eveniet",
    "sunt",
    "iure",
    "name",
    "nobis",
    "eum",
    "cum",
    "officiis",
    "excepturi",
    "odio",
    "consectetur",
    "quasi",
    "aut",
    "quisquam",
    "vel",
    "eligendi",
    "itaque",
    "non",
    "odit",
    "tempore",
    "quaerat",
    "dignissimos",
    "facilis",
    "neque",
    "nihil",
    "expedita",
    "vitae",
    "vero",
    "ipsum",
    "nisi",
    "animi",
    "cumque",
    "pariatur",
    "velit",
    "modi",
    "natus",
    "iusto",
    "eaque",
    "sequi",
    "illo",
    "sed",
    "ex",
    "et",
    "voluptatibus",
    "tempora",
    "veritatis",
    "ratione",
    "assumenda",
    "incidunt",
    "nostrum",
    "placeat",
    "aliquid",
    "fuga",
    "provident",
    "praesentium",
    "rem",
    "necessitatibus",
    "suscipit",
    "adipisci",
    "quidem",
    "possimus",
    "voluptas",
    "debitis",
    "sint",
    "accusantium",
    "unde",
    "sapiente",
    "voluptate",
    "qui",
    "aspernatur",
    "laudantium",
    "soluta",
    "amet",
    "quo",
    "aliquam",
    "saepe",
    "culpa",
    "libero",
    "ipsa",
    "dicta",
    "reiciendis",
    "nesciunt",
    "doloribus",
    "autem",
    "impedit",
    "minima",
    "maiores",
    "repudiandae",
    "ipsam",
    "obcaecati",
    "ullam",
    "enim",
    "totam",
    "delectus",
    "ducimus",
    "quis",
    "voluptates",
    "dolores",
    "molestiae",
    "harum",
    "dolorem",
    "quia",
    "voluptatem",
    "molestias",
    "magni",
    "distinctio",
    "omnis",
    "illum",
    "dolorum",
    "voluptatum",
    "ea",
    "quas",
    "quam",
    "corporis",
    "quae",
    "blanditiis",
    "atque",
    "deserunt",
    "laboriosam",
    "earum",
    "consequuntur",
    "hic",
    "cupiditate",
    "quibusdam",
    "accusamus",
    "ut",
    "rerum",
    "error",
    "minus",
    "eius",
    "ab",
    "ad",
    "nemo",
    "fugit",
    "officia",
    "at",
    "in",
    "id",
    "quos",
    "reprehenderit",
    "numquam",
    "iste",
    "fugiat",
    "sit",
    "inventore",
    "beatae",
    "repellendus",
    "magnam",
    "recusandae",
    "quod",
    "explicabo",
    "doloremque",
    "aperiam",
    "consequatur",
    "asperiores",
    "commodi",
    "option",
    "dolor",
    "labore",
    "temporibus",
    "repellat",
    "veniam",
    "architecto",
    "est",
    "esse",
    "mollitia",
    "nulla",
    "a",
    "similique",
    "eos",
    "alias",
    "dolore",
    "tenetur",
    "deleniti",
    "porro",
    "facere",
    "maxime",
    "corrupti",
];

static COMMON_WORDS: [&str; 19] = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipisicing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
];

pub fn sentence() -> String {
    use rand::Rng;
    use rand::seq::SliceRandom;

    let mut rng = rand::thread_rng();
    let num_sections = rng.gen_range(1..=5);
    let mut sections = Vec::with_capacity(num_sections);

    for _ in 0..num_sections {
        let num_words = rng.gen_range(3..=12);
        let selected_words: Vec<&str> = WORDS
            .choose_multiple(&mut rng, num_words)
            .copied()
            .collect();

        sections.push(selected_words.join(" "));
    }

    let mut sentence = sections.join(", ");

    if let Some(first) = sentence.chars().next() {
        let upper = first.to_uppercase();
        let rest = &sentence[first.len_utf8()..];
        sentence = format!("{upper}{rest}");
    }

    let punctuation = if rng.gen_bool(0.5) { "?" } else { "." };
    sentence.push_str(punctuation);

    sentence
}

pub fn paragraph() -> String {
    let num_sentences = rand::thread_rng().gen_range(1..=4);
    (0..num_sentences)
        .map(|_| sentence())
        .collect::<Vec<String>>()
        .join(" ")
}

pub fn paragraphs(count: usize, common: bool) -> Vec<Cow<'static, str>> {
    let mut paras = Vec::with_capacity(count);
    for i in 0..count {
        if common && i == 0 {
            paras.push(Cow::Borrowed(COMMON_P));
        } else {
            paras.push(Cow::Owned(paragraph()));
        }
    }

    paras
}

pub fn words(mut count: usize, common: bool) -> String {
    if common && count <= COMMON_WORDS.len() {
        return COMMON_WORDS[..count].join(" ");
    }
    let mut rng = rand::thread_rng();
    let mut word_list: Vec<&str> = Vec::with_capacity(count);
    if common {
        word_list.extend(&COMMON_WORDS);
        count -= word_list.len();
    }
    while count > 0 {
        let take = count.min(WORDS.len());
        let sampled = WORDS.choose_multiple(&mut rng, take);
        word_list.extend(sampled.copied());
        count -= take;
    }
    word_list.join(" ")
}

#[derive(Debug, PartialEq, Clone)]
pub struct LoremToken {
    pub at: At,
    pub count_at: Option<At>,
    pub method: LoremMethod,
    pub common: bool,
}

#[derive(Debug, PartialEq, Clone)]
pub enum LoremMethod {
    Words,
    Paragraphs,
    Blocks,
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum LoremError {
    #[error("Incorrect format for 'lorem' tag: count must come before method or random")]
    #[diagnostic(help("Move the count argument before the method"))]
    CountAfterMethodOrRandom {
        #[label("count must come first")]
        _at: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'random' was provided more than once")]
    #[diagnostic(help("Try removing the second 'random'"))]
    DuplicateRandom {
        #[label("first 'random'")]
        _first: SourceSpan,
        #[label("second 'random'")]
        _second: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'method' argument was provided more than once")]
    #[diagnostic(help("Try removing the second 'method'"))]
    DuplicateMethod {
        #[label("first 'method'")]
        _first: SourceSpan,
        #[label("second 'method'")]
        _second: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'count' argument was provided more than once")]
    #[diagnostic(help("Try removing the second 'count'"))]
    DuplicateCount {
        #[label("first 'count'")]
        _first: SourceSpan,
        #[label("second 'count'")]
        _second: SourceSpan,
    },
    #[error("Invalid filter: ''")]
    InvalidRemainder {
        #[label("expected filter name after '|'")]
        _at: SourceSpan,
    },
}

pub fn lex_lorem(template: TemplateString<'_>, parts: TagParts) -> Result<LoremToken, LoremError> {
    let content = template.content(parts.at);

    let mut words: Vec<(At, &str)> = Vec::new();
    let mut start = 0;

    while start < content.len() {
        if let Some(ws) = content[start..].find(|c: char| !c.is_whitespace()) {
            let actual = start + ws;
            let len = content[actual..]
                .find(char::is_whitespace)
                .unwrap_or(content.len() - actual);

            words.push(((parts.at.0 + actual, len), &content[actual..actual + len]));
            start = actual + len;
        } else {
            break;
        }
    }

    if words.len() == 1 {
        let (_at, text) = words[0];
        if matches!(text, "w" | "p" | "b") {
            return Ok(LoremToken {
                at: parts.at,
                count_at: None,
                method: match text {
                    "w" => LoremMethod::Words,
                    "p" => LoremMethod::Paragraphs,
                    _ => LoremMethod::Blocks,
                },
                common: true,
            });
        }
    }

    let mut count_at: Option<At> = None;
    let mut method_at: Option<At> = None;
    let mut random_at: Option<At> = None;
    let mut count_from_keyword = false;

    let mut method = LoremMethod::Blocks;
    let mut common = true;
    let mut is_first = true;

    for (at, text) in words {
        if is_first {
            is_first = false;
            count_at = Some(at);

            if matches!(text, "w" | "p" | "b" | "random") {
                count_from_keyword = true;
            }

            continue;
        }

        match text {
            "w" | "p" | "b" => {
                if let Some(first) = method_at {
                    return Err(LoremError::DuplicateMethod {
                        _first: first.into(),
                        _second: at.into(),
                    });
                }
                method_at = Some(at);
                method = match text {
                    "w" => LoremMethod::Words,
                    "p" => LoremMethod::Paragraphs,
                    _ => LoremMethod::Blocks,
                };
            }

            "random" => {
                if let Some(first) = random_at {
                    return Err(LoremError::DuplicateRandom {
                        _first: first.into(),
                        _second: at.into(),
                    });
                }
                random_at = Some(at);
                common = false;
            }

            _ => {
                if count_from_keyword {
                    return Err(LoremError::CountAfterMethodOrRandom { _at: at.into() });
                }

                return Err(LoremError::DuplicateCount {
                    _first: count_at.unwrap().into(),
                    _second: at.into(),
                });
            }
        }
    }

    Ok(LoremToken {
        at: parts.at,
        count_at,
        method,
        common,
    })
}
