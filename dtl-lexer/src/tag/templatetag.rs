#![expect(unused_assignments)]
use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementTokenType};
use crate::types::TemplateString;
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TemplateTag {
    OpenBlock,
    CloseBlock,
    OpenVariable,
    CloseVariable,
    OpenBrace,
    CloseBrace,
    OpenComment,
    CloseComment,
}

impl TemplateTag {
    pub fn output(&self) -> &'static str {
        match self {
            Self::OpenBlock => "{%",
            Self::CloseBlock => "%}",
            Self::OpenVariable => "{{",
            Self::CloseVariable => "}}",
            Self::OpenBrace => "{",
            Self::CloseBrace => "}",
            Self::OpenComment => "{#",
            Self::CloseComment => "#}",
        }
    }
}

pub fn lex_templatetag(
    template: TemplateString<'_>,
    parts: TagParts,
) -> Result<TemplateTag, TemplateTagError> {
    let mut lexer = TagElementLexer::new(template, parts.clone());

    let Some(token) = lexer.next().transpose()? else {
        return Err(TemplateTagError::MissingArgument {
            at: parts.at.into(),
        });
    };

    let content = template.content(token.at);

    if token.token_type != TagElementTokenType::Variable {
        return Err(TemplateTagError::InvalidArgument {
            argument: content.to_string(),
            at: token.at.into(),
        });
    }

    let tag_type = match content {
        "openblock" => TemplateTag::OpenBlock,
        "closeblock" => TemplateTag::CloseBlock,
        "openvariable" => TemplateTag::OpenVariable,
        "closevariable" => TemplateTag::CloseVariable,
        "openbrace" => TemplateTag::OpenBrace,
        "closebrace" => TemplateTag::CloseBrace,
        "opencomment" => TemplateTag::OpenComment,
        "closecomment" => TemplateTag::CloseComment,
        _ => {
            return Err(TemplateTagError::InvalidArgument {
                argument: content.to_string(),
                at: token.at.into(),
            })
        }
    };

    if let Some(token) = lexer.next().transpose()? {
        return Err(TemplateTagError::ExtraArgument {
            at: token.at.into(),
        });
    }

    Ok(tag_type)
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum TemplateTagError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),

    #[error("'templatetag' statement takes one argument")]
    MissingArgument {
        #[label("missing argument")]
        at: SourceSpan,
    },

    #[error("Invalid templatetag argument: '{argument}'")]
    #[diagnostic(help(
        "Must be one of: openblock, closeblock, openvariable, closevariable, openbrace, closebrace, opencomment, closecomment"
    ))]
    InvalidArgument {
        argument: String,
        #[label("invalid argument")]
        at: SourceSpan,
    },

    #[error("'templatetag' statement takes one argument")]
    ExtraArgument {
        #[label("extra argument")]
        at: SourceSpan,
    },
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::IntoTemplateString;

    #[test]
    fn test_lex_openblock() {
        let template = "{% templatetag openblock %}";
        let parts = TagParts { at: (15, 9) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::OpenBlock);
    }

    #[test]
    fn test_lex_closeblock() {
        let template = "{% templatetag closeblock %}";
        let parts = TagParts { at: (15, 10) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::CloseBlock);
    }

    #[test]
    fn test_lex_openvariable() {
        let template = "{% templatetag openvariable %}";
        let parts = TagParts { at: (15, 12) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::OpenVariable);
    }

    #[test]
    fn test_lex_closevariable() {
        let template = "{% templatetag closevariable %}";
        let parts = TagParts { at: (15, 13) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::CloseVariable);
    }

    #[test]
    fn test_lex_openbrace() {
        let template = "{% templatetag openbrace %}";
        let parts = TagParts { at: (15, 9) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::OpenBrace);
    }

    #[test]
    fn test_lex_closebrace() {
        let template = "{% templatetag closebrace %}";
        let parts = TagParts { at: (15, 10) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::CloseBrace);
    }

    #[test]
    fn test_lex_opencomment() {
        let template = "{% templatetag opencomment %}";
        let parts = TagParts { at: (15, 11) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::OpenComment);
    }

    #[test]
    fn test_lex_closecomment() {
        let template = "{% templatetag closecomment %}";
        let parts = TagParts { at: (15, 12) };
        let tag_type = lex_templatetag(template.into_template_string(), parts).unwrap();
        assert_eq!(tag_type, TemplateTag::CloseComment);
    }

    #[test]
    fn test_lex_missing_argument() {
        let template = "{% templatetag %}";
        let parts = TagParts { at: (15, 0) };
        assert!(matches!(
            lex_templatetag(template.into_template_string(), parts),
            Err(TemplateTagError::MissingArgument { .. })
        ));
    }

    #[test]
    fn test_lex_invalid_argument() {
        let template = "{% templatetag invalid %}";
        let parts = TagParts { at: (15, 7) };
        assert!(matches!(
            lex_templatetag(template.into_template_string(), parts),
            Err(TemplateTagError::InvalidArgument { .. })
        ));
    }

    #[test]
    fn test_lex_extra_argument() {
        let template = "{% templatetag openblock extra %}";
        let parts = TagParts { at: (15, 15) };
        assert!(matches!(
            lex_templatetag(template.into_template_string(), parts),
            Err(TemplateTagError::ExtraArgument { .. })
        ));
    }

    #[test]
    fn test_lex_string_argument_is_invalid() {
        let template = r#"{% templatetag "openblock" %}"#;
        let parts = TagParts { at: (15, 11) };
        assert!(matches!(
            lex_templatetag(template.into_template_string(), parts),
            Err(TemplateTagError::InvalidArgument { .. })
        ));
    }
}
