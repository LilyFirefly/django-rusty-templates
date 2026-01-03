use crate::tag::TagParts;
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Debug, PartialEq, Clone)]
pub enum LoremMethod {
    Words,
    Paragraphs,
    Blocks,
}

#[derive(Debug, PartialEq, Clone)]
pub enum LoremTokenType {
    Count,
    Method(LoremMethod),
    Random,
}

#[derive(Debug, PartialEq, Clone)]
pub struct LoremToken {
    pub at: At,
    pub token_type: LoremTokenType,
}

pub struct LoremLexer<'t> {
    words: Vec<(At, &'t str)>,
    index: usize,
}

impl<'t> LoremLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        let content = template.content(parts.at);

        let mut words = Vec::new();
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

        Self { words, index: 0 }
    }
}

impl<'t> Iterator for LoremLexer<'t> {
    type Item = LoremToken;

    fn next(&mut self) -> Option<Self::Item> {
        let (at, text) = *self.words.get(self.index)?;
        self.index += 1;

        let token_type = match text {
            "w" => LoremTokenType::Method(LoremMethod::Words),
            "p" => LoremTokenType::Method(LoremMethod::Paragraphs),
            "b" => LoremTokenType::Method(LoremMethod::Blocks),
            "random" => LoremTokenType::Random,
            _ => LoremTokenType::Count,
        };

        Some(LoremToken { at, token_type })
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum LoremError {
    #[error("Incorrect format for 'lorem' tag: 'count' must come before the 'method' argument")]
    #[diagnostic(help("Move the 'count' argument before the 'method' argument"))]
    CountAfterMethod {
        #[label("method")]
        _method_at: SourceSpan,
        #[label("count")]
        _count_at: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'count' must come before the 'random' argument")]
    #[diagnostic(help("Move the 'count' argument before the 'random' argument"))]
    CountAfterRandom {
        #[label("random")]
        _random_at: SourceSpan,
        #[label("count")]
        _count_at: SourceSpan,
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
}
