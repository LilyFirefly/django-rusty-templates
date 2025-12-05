use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::tag::TagParts;
use crate::types::{At, TemplateString};

#[derive(Clone, Debug, PartialEq)]
pub enum AutoescapeEnabled {
    On,
    Off,
}

impl From<&AutoescapeEnabled> for bool {
    fn from(enabled: &AutoescapeEnabled) -> Self {
        match enabled {
            AutoescapeEnabled::On => true,
            AutoescapeEnabled::Off => false,
        }
    }
}

#[derive(Debug, PartialEq)]
pub struct AutoescapeToken {
    pub at: At,
    pub enabled: AutoescapeEnabled,
}

#[allow(clippy::enum_variant_names)] // https://github.com/rust-lang/rust-clippy/issues/10599
#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum AutoescapeError {
    #[error("'autoescape' argument should be 'on' or 'off'.")]
    InvalidArgument {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'autoescape' tag missing an 'on' or 'off' argument.")]
    MissingArgument {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'autoescape' tag requires exactly one argument.")]
    UnexpectedArgument {
        #[label("here")]
        at: SourceSpan,
    },
}

pub fn lex_autoescape_argument(
    template: TemplateString<'_>,
    parts: TagParts,
) -> Result<AutoescapeToken, AutoescapeError> {
    let content = template.content(parts.at);
    let at = parts.at;
    match content {
        "off" => Ok(AutoescapeToken {
            at,
            enabled: AutoescapeEnabled::Off,
        }),
        "on" => Ok(AutoescapeToken {
            at,
            enabled: AutoescapeEnabled::On,
        }),
        "" => Err(AutoescapeError::MissingArgument { at: at.into() }),
        _ => match content.find(char::is_whitespace) {
            None => Err(AutoescapeError::InvalidArgument { at: at.into() }),
            Some(_) => Err(AutoescapeError::UnexpectedArgument { at: at.into() }),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lex_autoescape_off() {
        let template = "{% autoescape off %}";
        let parts = TagParts { at: (14, 3) };
        let token = lex_autoescape_argument(template.into(), parts).unwrap();
        let off = AutoescapeToken {
            at: (14, 3),
            enabled: AutoescapeEnabled::Off,
        };
        assert_eq!(token, off);
    }

    #[test]
    fn test_lex_autoescape_on() {
        let template = "{% autoescape on %}";
        let parts = TagParts { at: (14, 2) };
        let token = lex_autoescape_argument(template.into(), parts).unwrap();
        let on = AutoescapeToken {
            at: (14, 2),
            enabled: AutoescapeEnabled::On,
        };
        assert_eq!(token, on);
    }

    #[test]
    fn test_lex_autoescape_empty() {
        let template = "{% autoescape %}";
        let parts = TagParts { at: (8, 0) };
        let error = lex_autoescape_argument(template.into(), parts).unwrap_err();
        assert_eq!(
            error,
            AutoescapeError::MissingArgument { at: (8, 0).into() }
        );
    }

    #[test]
    fn test_lex_autoescape_invalid() {
        let template = "{% autoescape other %}";
        let parts = TagParts { at: (14, 5) };
        let error = lex_autoescape_argument(template.into(), parts).unwrap_err();
        assert_eq!(
            error,
            AutoescapeError::InvalidArgument { at: (14, 5).into() }
        );
    }

    #[test]
    fn test_lex_autoescape_unexpected_argument() {
        let template = "{% autoescape off on %}";
        let parts = TagParts { at: (14, 6) };
        let error = lex_autoescape_argument(template.into(), parts).unwrap_err();
        assert_eq!(
            error,
            AutoescapeError::UnexpectedArgument { at: (14, 6).into() }
        );
    }
}
