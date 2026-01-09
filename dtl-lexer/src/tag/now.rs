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
            return Err(NowError::MissingFormat {
                _at: self.parts.at.into(),
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
                    let position_after_as = token.at.0 + token.at.1;
                    return Err(NowError::MissingVariableAfterAs {
                        _at: SourceSpan::new(position_after_as.into(), 0usize),
                    });
                };

                check_variable_attrs(self.template.content(var.at), var.at.0)?;

                Ok(Some(var.at))
            }
            _ => Err(NowError::UnexpectedAfterFormat {
                _at: token.at.into(),
            }),
        }
    }

    pub fn extra_token(&mut self) -> Result<Option<TagElementToken>, NowError> {
        match self.next_element()? {
            None => Ok(None),
            Some(token) => Err(NowError::UnexpectedAfterVariable {
                _at: token.at.into(),
            }),
        }
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum NowError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),

    #[error("Unexpected argument after format string")]
    #[diagnostic(help("If you want to store the result in a variable, use the 'as' keyword."))]
    UnexpectedAfterFormat {
        #[label("unexpected argument")]
        _at: SourceSpan,
    },

    #[error("Expected a variable name after 'as'")]
    #[diagnostic(help("Provide a name to store the date string, e.g. 'as my_var'"))]
    MissingVariableAfterAs {
        #[label("expected a variable name here")]
        _at: SourceSpan,
    },

    #[error("Unexpected argument after variable name")]
    #[diagnostic(help(
        "The 'now' tag only accepts one variable assignment. Try removing this extra argument."
    ))]
    UnexpectedAfterVariable {
        #[label("extra argument")]
        _at: SourceSpan,
    },

    #[error("Expected a format string")]
    #[diagnostic(help(
        "The 'now' tag requires a format string, like \"Y-m-d\" or \"DATE_FORMAT\"."
    ))]
    MissingFormat {
        #[label("missing format")]
        _at: SourceSpan,
    },
}
