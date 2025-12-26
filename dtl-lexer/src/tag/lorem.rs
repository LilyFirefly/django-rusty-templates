use miette::{Diagnostic, SourceSpan};
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

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum LoremError {
    #[error("Incorrect format for 'lorem' tag")]
    #[label("here")]
    InvalidFormat { at: SourceSpan },
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

    let mut count_at: Option<At> = None;
    let mut method = LoremMethod::Blocks;
    let mut common = true;

    let mut seen_count = false;
    let mut seen_method = false;
    let mut seen_random = false;

    let mut i = 0;
    while i < words.len() {
        let (at, text) = words[i];

        match text {
            "w" | "p" | "b" => {
                if seen_method {
                    return Err(LoremError::InvalidFormat { at: at.into() });
                }
                seen_method = true;
                method = match text {
                    "w" => LoremMethod::Words,
                    "p" => LoremMethod::Paragraphs,
                    _ => LoremMethod::Blocks,
                };
            }
            "random" => {
                if seen_random {
                    return Err(LoremError::InvalidFormat { at: at.into() });
                }
                seen_random = true;
                common = false;
            }
            _ => {
                if text.chars().all(|c| c.is_ascii_digit()) {
                    if seen_random {
                        return Err(LoremError::InvalidFormat { at: at.into() });
                    }
                    if seen_method {
                        return Err(LoremError::InvalidFormat { at: at.into() });
                    }
                    if seen_count {
                        return Err(LoremError::InvalidFormat { at: at.into() });
                    }
                    seen_count = true;
                    count_at = Some(at);
                }
            }
        }

        i += 1;
    }

    Ok(LoremToken {
        at: parts.at,
        count_at,
        method,
        common,
    })
}
