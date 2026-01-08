use crate::common::{LexerError, check_variable_attrs};
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Now {
    pub format_at: At,
    pub asvar: Option<At>,
}

pub struct NowLexer<'t> {
    template: TemplateString<'t>,
    lexer: TagElementLexer<'t>,
    parts: TagParts,
}

impl<'t> NowLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            template,
            lexer: TagElementLexer::new(template, parts.clone()),
            parts,
        }
    }

    fn next_element(&mut self) -> Result<Option<TagElementToken>, NowError> {
        match self.lexer.next() {
            None => Ok(None),
            Some(Ok(token)) => Ok(Some(token)),
            Some(Err(err)) => Err(err.into()),
        }
    }

    pub fn lex_format(&mut self) -> Result<At, NowError> {
        let Some(token) = self.next_element()? else {
            return Err(NowError::Syntax {
                at: self.parts.at.into(),
            });
        };
        Ok(token.at)
    }

    pub fn lex_variable(&mut self) -> Result<Option<At>, NowError> {
        let Some(token) = self.next_element()? else {
            return Ok(None);
        };

        match self.template.content(token.at) {
            "as" => {
                let Some(var) = self.next_element()? else {
                    return Err(NowError::Syntax {
                        at: token.at.into(),
                    });
                };

                check_variable_attrs(self.template.content(var.at), var.at.0)?;

                Ok(Some(var.at))
            }
            _ => Err(NowError::Syntax {
                at: token.at.into(),
            }),
        }
    }

    pub fn extra_token(&mut self) -> Result<Option<TagElementToken>, NowError> {
        self.next_element()
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum NowError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),

    #[error("'now' statement takes one argument")]
    Syntax {
        #[label("here")]
        at: SourceSpan,
    },
}
