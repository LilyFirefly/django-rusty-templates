#![expect(unused_assignments)]
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::common::NextChar;
use crate::tag::TagParts;
use crate::types::{At, TemplateString};

#[derive(Debug, PartialEq)]
pub struct BlockToken {
    pub at: At,
}

#[derive(Debug, Error, Diagnostic, PartialEq, Eq)]
pub enum BlockLexerError {
    #[error("'{name}' tag takes only one argument")]
    UnexpectedArguments {
        name: &'static str,
        #[label("unexpected argument(s)")]
        at: SourceSpan,
    },
}

pub enum BlockType {
    Start,
    End,
}

pub fn lex_block(
    template: TemplateString,
    parts: TagParts,
    block_type: BlockType,
) -> Result<Option<BlockToken>, BlockLexerError> {
    let rest = template.content(parts.at);
    if rest.is_empty() {
        return Ok(None);
    }

    let len = rest.next_whitespace();
    let rest = &rest[len..];
    let next = rest.next_non_whitespace();
    let rest = &rest[next..];
    if rest.is_empty() {
        let at = (parts.at.0, len);
        Ok(Some(BlockToken { at }))
    } else {
        let at = (parts.at.0 + len + next, rest.len());
        let name = match block_type {
            BlockType::Start => "block",
            BlockType::End => "endblock",
        };
        Err(BlockLexerError::UnexpectedArguments {
            at: at.into(),
            name,
        })
    }
}
