use thiserror::Error;

use crate::tag::TagParts;
use crate::types::{At, TemplateString};

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

#[derive(Debug, Error, PartialEq, Eq)]
pub enum LoremError {
    #[error("Invalid format for 'lorem' tag")]
    InvalidFormat { at: At },

    #[error("Incorrect format for 'lorem' tag: 'random' was provided more than once")]
    DuplicateRandom { first: At, second: At },

    #[error("Incorrect format for 'lorem' tag: 'method' argument was provided more than once")]
    DuplicateMethod { first: At, second: At },

    #[error("Incorrect format for 'lorem' tag: 'count' argument was provided more than once")]
    DuplicateCount { first: At, second: At },
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

    // {% lorem w %} special case
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
                    return Err(LoremError::DuplicateMethod { first, second: at });
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
                    return Err(LoremError::DuplicateRandom { first, second: at });
                }
                random_at = Some(at);
                common = false;
            }

            _ => {
                if count_from_keyword {
                    return Err(LoremError::InvalidFormat { at });
                }

                return Err(LoremError::DuplicateCount {
                    first: count_at.unwrap(),
                    second: at,
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
