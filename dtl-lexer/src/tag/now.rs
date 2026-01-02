use crate::tag::TagParts;
use crate::tag::custom_tag::{SimpleTagLexer, SimpleTagTokenType};
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("'now' statement takes one argument")]
pub struct NowSyntaxError {
    #[label("here")]
    pub at: SourceSpan,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Now {
    pub format_at: At,
    pub asvar: Option<At>,
}

pub fn lex_now(template: TemplateString<'_>, parts: TagParts) -> Result<Now, NowSyntaxError> {
    let at = parts.at;

    let mut lexer = SimpleTagLexer::new(template, parts);

    let Some(token) = lexer.next() else {
        return Err(NowSyntaxError { at: at.into() });
    };

    let token = token.map_err(|_| NowSyntaxError { at: at.into() })?;

    if token.token_type != SimpleTagTokenType::Text {
        return Err(NowSyntaxError {
            at: token.at.into(),
        });
    }

    let format_at = token.at;
    let mut asvar = None;

    if let Some(next) = lexer.next() {
        let next = next.map_err(|_| NowSyntaxError { at: at.into() })?;

        if next.token_type != SimpleTagTokenType::Variable || template.content(next.at) != "as" {
            return Err(NowSyntaxError { at: next.at.into() });
        }

        let Some(var) = lexer.next() else {
            return Err(NowSyntaxError { at: next.at.into() });
        };

        let var = var.map_err(|_| NowSyntaxError { at: next.at.into() })?;

        asvar = Some(var.at);

        if let Some(extra) = lexer.next() {
            let extra = extra.map_err(|_| NowSyntaxError { at: at.into() })?;
            return Err(NowSyntaxError {
                at: extra.at.into(),
            });
        }
    }

    Ok(Now { format_at, asvar })
}
