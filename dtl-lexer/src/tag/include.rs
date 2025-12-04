use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::common::{text_content_at, translated_text_content_at};
use crate::tag::TagParts;
use crate::tag::custom_tag::{SimpleTagLexer, SimpleTagLexerError, SimpleTagTokenType};
use crate::types::{At, TemplateString};

#[derive(Debug, PartialEq, Eq)]
pub enum IncludeTemplateTokenType {
    Text,
    TranslatedText,
    Variable,
}

#[derive(Debug, PartialEq, Eq)]
pub struct IncludeTemplateToken {
    pub at: At,
    pub token_type: IncludeTemplateTokenType,
}

impl IncludeTemplateToken {
    pub fn content_at(&self) -> At {
        match self.token_type {
            IncludeTemplateTokenType::Variable => self.at,
            IncludeTemplateTokenType::Text => text_content_at(self.at),
            IncludeTemplateTokenType::TranslatedText => translated_text_content_at(self.at),
        }
    }
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum IncludeLexerError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    SimpleTagLexerError(#[from] SimpleTagLexerError),
    #[error("Included template name must be a string or iterable of strings.")]
    InvalidTemplateName {
        #[label("invalid template name")]
        at: SourceSpan,
    },
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
            None => {
                let token_type = match token.token_type {
                    SimpleTagTokenType::Numeric => {
                        return Err(IncludeLexerError::InvalidTemplateName {
                            at: token.at.into(),
                        });
                    }
                    SimpleTagTokenType::Text => IncludeTemplateTokenType::Text,
                    SimpleTagTokenType::TranslatedText => IncludeTemplateTokenType::TranslatedText,
                    SimpleTagTokenType::Variable => IncludeTemplateTokenType::Variable,
                };
                Ok(Some(IncludeTemplateToken {
                    at: token.at,
                    token_type,
                }))
            }
        }
    }
}
