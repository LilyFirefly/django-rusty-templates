use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum CycleLexerError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),

    #[error("Invalid flag '{flag}' after cycle name")]
    #[diagnostic(help("Only the 'silent' flag is allowed here."))]
    InvalidFlag {
        flag: String,
        #[label("invalid flag")]
        at: SourceSpan,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub enum CycleArguments {
    Reference {
        name: At,
    },
    Definition {
        values: Vec<TagElementToken>,
        name: Option<At>,
        silent: bool,
    },
}

pub struct CycleLexer<'t> {
    template: TemplateString<'t>,
    lexer: TagElementLexer<'t>,
}

impl<'t> CycleLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            template,
            lexer: TagElementLexer::new(template, parts),
        }
    }

    pub fn tokens(&mut self) -> Result<Vec<TagElementToken>, LexerError> {
        self.lexer.by_ref().collect()
    }

    pub fn lex(mut self) -> Result<Option<CycleArguments>, CycleLexerError> {
        let mut tokens = self.tokens()?;
        match tokens.len() {
            0 => Ok(None),
            1 => Ok(Some(CycleArguments::Reference { name: tokens[0].at })),
            _ => {
                let named_suffix = match tokens.as_slice() {
                    [values @ .., as_token, name_token, flag_token]
                        if values.len() >= 2 && self.template.content(as_token.at) == "as" =>
                    {
                        let flag = self.template.content(flag_token.at);

                        if flag != "silent" {
                            return Err(CycleLexerError::InvalidFlag {
                                flag: flag.to_string(),
                                at: flag_token.at.into(),
                            });
                        }

                        Some((values.len(), name_token.at, true))
                    }

                    [values @ .., as_token, name_token]
                        if values.len() >= 2 && self.template.content(as_token.at) == "as" =>
                    {
                        Some((values.len(), name_token.at, false))
                    }
                    _ => None,
                };

                if let Some((value_count, name, silent)) = named_suffix {
                    tokens.truncate(value_count);

                    Ok(Some(CycleArguments::Definition {
                        values: tokens,
                        name: Some(name),
                        silent,
                    }))
                } else {
                    Ok(Some(CycleArguments::Definition {
                        values: tokens,
                        name: None,
                        silent: false,
                    }))
                }
            }
        }
    }
}
