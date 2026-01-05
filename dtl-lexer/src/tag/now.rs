use crate::common::NextChar;
use crate::tag::TagParts;
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Now {
    pub format_at: At,
    pub asvar: Option<At>,
}

#[derive(Debug, PartialEq, Clone)]
pub enum NowTokenType {
    Format,
    As,
    Variable,
}

#[derive(Debug, PartialEq, Clone)]
pub struct NowToken {
    pub at: At,
    pub token_type: NowTokenType,
}

pub struct NowLexer<'t> {
    rest: &'t str,
    byte: usize,
    seen_format: bool,
    seen_as: bool,
    seen_variable: bool,
}

impl<'t> NowLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        let content = template.content(parts.at);
        let skip = content.next_non_whitespace();
        Self {
            rest: &content[skip..],
            byte: parts.at.0 + skip,
            seen_format: false,
            seen_as: false,
            seen_variable: false,
        }
    }
}

impl<'t> Iterator for NowLexer<'t> {
    type Item = Result<NowToken, NowError>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.rest.is_empty() {
            return None;
        }

        let first_char = self.rest.chars().next()?;

        let len = if first_char == '"' || first_char == '\'' {
            match self.rest[1..].find(first_char) {
                Some(end_idx) => end_idx + 2, // here +1 for skip and +1 for closing quote
                None => self.rest.len(),      // Unclosed quote
            }
        } else {
            self.rest.next_whitespace()
        };

        let at = (self.byte, len);
        let content = &self.rest[..len];

        let token_type = if !self.seen_format {
            self.seen_format = true;
            Ok(NowTokenType::Format)
        } else if content == "as" && !self.seen_as {
            self.seen_as = true;
            Ok(NowTokenType::As)
        } else if self.seen_as && !self.seen_variable {
            self.seen_variable = true;
            Ok(NowTokenType::Variable)
        } else {
            Err(NowError::Syntax { at: at.into() })
        };

        let token_type = match token_type {
            Ok(t) => t,
            Err(e) => {
                self.rest = "";
                return Some(Err(e));
            }
        };

        let rest = &self.rest[len..];
        let next_skip = rest.next_non_whitespace();
        self.rest = &rest[next_skip..];
        self.byte = self.byte + len + next_skip;

        Some(Ok(NowToken { at, token_type }))
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum NowError {
    #[error("'now' statement takes one argument")]
    Syntax {
        #[label("here")]
        at: SourceSpan,
    },
}
