#![expect(unused_assignments)]
use crate::common::{LexerError, check_variable_attrs};
use crate::tag::TagParts;
use crate::tag::common::TagElementTokenType::Variable;
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
        self.lexer.next().transpose().or_else(|err| match err {
            LexerError::IncompleteString { at } => Ok(Some(TagElementToken {
                at: (at.offset(), at.len()),
                token_type: Variable,
            })),
            // TODO: Django's tokenizer does not treats {% now "Y"invalid %} as lexical error.
            //       We match this behavior here for compatibility, but this should be reverted to a strict LexerError
            //       if Django's parser becomes more strict in the future.
            LexerError::InvalidRemainder { at, .. } => {
                let start_of_tag = self.parts.at.0;
                let end_of_junk = at.offset() + at.len();

                let total_len = end_of_junk - start_of_tag;

                Ok(Some(TagElementToken {
                    at: (start_of_tag, total_len),
                    token_type: Variable,
                }))
            }
            _ => Err(err.into()),
        })
    }

    pub fn lex_format(&mut self) -> Result<At, NowError> {
        let Some(token) = self.next_element()? else {
            return Err(NowError::MissingFormat {
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
                    let position_after_as = token.at.0 + token.at.1;
                    return Err(NowError::MissingVariableAfterAs {
                        at: SourceSpan::new(position_after_as.into(), 0usize),
                    });
                };

                check_variable_attrs(self.template.content(var.at), var.at.0)?;

                Ok(Some(var.at))
            }
            _ => Err(NowError::UnexpectedAfterFormat {
                at: token.at.into(),
            }),
        }
    }

    pub fn extra_token(&mut self) -> Result<Option<TagElementToken>, NowError> {
        match self.next_element()? {
            None => Ok(None),
            Some(token) => Err(NowError::UnexpectedAfterVariable {
                at: token.at.into(),
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
        at: SourceSpan,
    },

    #[error("Expected a variable name after 'as'")]
    #[diagnostic(help("Provide a name to store the date string, e.g. 'as my_var'"))]
    MissingVariableAfterAs {
        #[label("expected a variable name here")]
        at: SourceSpan,
    },

    #[error("Unexpected argument after variable name")]
    #[diagnostic(help(
        "The 'now' tag only accepts one variable assignment. Try removing this extra argument."
    ))]
    UnexpectedAfterVariable {
        #[label("extra argument")]
        at: SourceSpan,
    },

    #[error("Expected a format string")]
    #[diagnostic(help(
        "The 'now' tag requires a format string, like \"Y-m-d\" or \"DATE_FORMAT\"."
    ))]
    MissingFormat {
        #[label("missing format")]
        at: SourceSpan,
    },
}
