use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::tag::TagParts;
use crate::types::{At, TemplateString};

#[derive(Debug, PartialEq)]
pub struct CycleToken {
    pub at: At,
    pub expressions: Vec<At>,
    pub name: Option<At>,
    pub silent: bool,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum CycleError {
    #[error("'cycle' tag requires at least two arguments.")]
    TooFewArguments {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'cycle' tag with 'as' requires a variable name.")]
    MissingAsName {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Only 'silent' flag is allowed after cycle's name, not '{flag}'.")]
    InvalidFlag {
        flag: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Named cycle '{name}' does not exist.")]
    UnknownNamedCycle {
        name: String,
        #[label("here")]
        at: SourceSpan,
    },
}

pub fn lex_cycle(
    template: TemplateString<'_>,
    parts: TagParts,
) -> Result<CycleToken, CycleError> {
    // TODO: LOGIC 

    Ok(CycleToken {
        at: parts.at,
        expressions,
        name,
        silent,
    })
}