use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::common::{text_content_at, translated_text_content_at};
use crate::custom_tag::{SimpleTagLexer, SimpleTagLexerError, SimpleTagTokenType};
use crate::tag::TagParts;
use crate::types::TemplateString;

pub struct IncludeTemplateToken {
    pub at: (usize, usize),
    pub token_type: SimpleTagTokenType,
}

impl IncludeTemplateToken {
    pub fn content_at(&self) -> (usize, usize) {
        match self.token_type {
            SimpleTagTokenType::Variable => self.at,
            SimpleTagTokenType::Numeric => self.at,
            SimpleTagTokenType::Text => text_content_at(self.at),
            SimpleTagTokenType::TranslatedText => translated_text_content_at(self.at),
        }
    }
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum IncludeLexerError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    SimpleTagLexerError(#[from] SimpleTagLexerError),
    #[error("Unexpected keyword argument")]
    UnexpectedKeywordArgument {
        #[label("here")]
        at: SourceSpan,
    },
}

pub struct IncludeLexer<'t>(SimpleTagLexer<'t>);

impl<'t> IncludeLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self(SimpleTagLexer::new(template, parts))
    }

    pub fn lex_template(&mut self) -> Result<Option<IncludeTemplateToken>, IncludeLexerError> {
        let token = match self.0.next() {
            Some(token) => token?,
            None => return Ok(None),
        };
        match token.kwarg {
            Some(kwarg_at) => Err(IncludeLexerError::UnexpectedKeywordArgument {
                at: kwarg_at.into(),
            }),
            None => Ok(Some(IncludeTemplateToken {
                at: token.at,
                token_type: token.token_type,
            })),
        }
    }
}
