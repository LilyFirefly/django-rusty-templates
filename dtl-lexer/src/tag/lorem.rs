#![expect(unused_assignments)]
use crate::common::NextChar;
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
    rest: &'t str,
    byte: usize,
    seen_count: Option<At>,
    seen_method: Option<At>,
    seen_random: Option<At>,
}

impl<'t> LoremLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            rest: template.content(parts.at),
            byte: parts.at.0,
            seen_count: None,
            seen_method: None,
            seen_random: None,
        }
    }

    fn check_method(&mut self, method: LoremMethod, at: At) -> Result<LoremTokenType, LoremError> {
        if let Some(random_at) = self.seen_random {
            match self.seen_count {
                Some(_) => {
                    return Err(LoremError::MethodAfterRandom {
                        method_at: at.into(),
                        random_at: random_at.into(),
                    });
                }
                None => self.seen_count = Some(random_at),
            }
        }

        if let Some(method_at) = self.seen_method {
            match self.seen_count {
                Some(_) => {
                    return Err(LoremError::DuplicateMethod {
                        first: method_at.into(),
                        second: at.into(),
                    });
                }
                None => self.seen_count = Some(method_at),
            }
        }
        self.seen_method = Some(at);
        Ok(LoremTokenType::Method(method))
    }

    fn check_random(&mut self, at: At) -> Result<LoremTokenType, LoremError> {
        if let Some(random_at) = self.seen_random {
            match self.seen_count {
                Some(_) => {
                    return Err(LoremError::DuplicateRandom {
                        first: random_at.into(),
                        second: at.into(),
                    });
                }
                None => self.seen_count = Some(random_at),
            }
        }
        self.seen_random = Some(at);
        Ok(LoremTokenType::Random)
    }

    fn check_count(&mut self, count_at: At) -> Result<LoremTokenType, LoremError> {
        if let Some(first_count_at) = self.seen_count {
            return Err(LoremError::DuplicateCount {
                first: first_count_at.into(),
                second: count_at.into(),
            });
        }

        if let Some(method_at) = self.seen_method {
            return Err(LoremError::CountAfterMethod {
                count_at: count_at.into(),
                method_at: method_at.into(),
            });
        }

        if let Some(random_at) = self.seen_random {
            return Err(LoremError::CountAfterRandom {
                count_at: count_at.into(),
                random_at: random_at.into(),
            });
        }

        self.seen_count = Some(count_at);
        Ok(LoremTokenType::Count)
    }
}

impl<'t> Iterator for LoremLexer<'t> {
    type Item = Result<LoremToken, LoremError>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.rest.is_empty() {
            return None;
        }

        let len = self.rest.next_whitespace();
        let at = (self.byte, len);
        let token_type = match &self.rest[..len] {
            "w" => self.check_method(LoremMethod::Words, at),
            "p" => self.check_method(LoremMethod::Paragraphs, at),
            "b" => self.check_method(LoremMethod::Blocks, at),
            "random" => self.check_random(at),
            _ => self.check_count(at),
        };
        let token_type = match token_type {
            Ok(token_type) => token_type,
            Err(err) => {
                self.rest = "";
                return Some(Err(err));
            }
        };

        let rest = &self.rest[len..];
        let next = rest.next_non_whitespace();
        self.rest = &rest[next..];
        self.byte = self.byte + len + next;

        Some(Ok(LoremToken { at, token_type }))
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum LoremError {
    #[error("Incorrect format for 'lorem' tag: 'count' must come before the 'method' argument")]
    #[diagnostic(help("Move the 'count' argument before the 'method' argument"))]
    CountAfterMethod {
        #[label("method")]
        method_at: SourceSpan,
        #[label("count")]
        count_at: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'count' must come before the 'random' argument")]
    #[diagnostic(help("Move the 'count' argument before the 'random' argument"))]
    CountAfterRandom {
        #[label("random")]
        random_at: SourceSpan,
        #[label("count")]
        count_at: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'method' must come before the 'random' argument")]
    #[diagnostic(help("Move the 'method' argument before the 'random' argument"))]
    MethodAfterRandom {
        #[label("random")]
        random_at: SourceSpan,
        #[label("method")]
        method_at: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'random' was provided more than once")]
    #[diagnostic(help("Try removing the second 'random'"))]
    DuplicateRandom {
        #[label("first 'random'")]
        first: SourceSpan,
        #[label("second 'random'")]
        second: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'method' argument was provided more than once")]
    #[diagnostic(help("Try removing the second 'method'"))]
    DuplicateMethod {
        #[label("first 'method'")]
        first: SourceSpan,
        #[label("second 'method'")]
        second: SourceSpan,
    },

    #[error("Incorrect format for 'lorem' tag: 'count' argument was provided more than once")]
    #[diagnostic(help("Try removing the second 'count'"))]
    DuplicateCount {
        #[label("first 'count'")]
        first: SourceSpan,
        #[label("second 'count'")]
        second: SourceSpan,
    },
}
