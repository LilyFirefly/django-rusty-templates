pub mod autoescape;
pub mod common;
pub mod forloop;
pub mod ifcondition;
pub mod include;
pub mod kwarg;
pub mod load;
pub mod lorem;
pub mod now;

use crate::common::NextChar;
use crate::types::{At, TemplateString};
use crate::{END_TAG_LEN, START_TAG_LEN, TemplateContent};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;
use unicode_xid::UnicodeXID;

#[derive(Error, Debug, Diagnostic, Eq, PartialEq)]
pub enum TagLexerError {
    #[error("Invalid block tag name")]
    InvalidTagName {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Empty block tag")]
    EmptyTag {
        #[label("here")]
        at: SourceSpan,
    },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TagParts {
    pub at: At,
}

impl<'t> TemplateContent<'t> for TagParts {
    fn content(&self, template: TemplateString<'t>) -> &'t str {
        template.content(self.at)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Tag {
    pub at: At,
    pub parts: TagParts,
}

impl<'t> TemplateContent<'t> for Tag {
    fn content(&self, template: TemplateString<'t>) -> &'t str {
        template.content(self.at)
    }
}

/// Tokenize the template source between `{%` and `%}` into a `Tag`.
///
/// A `Tag` has two pieces:
/// * `at` representing the location of the tag name
/// * `parts` representing the location of the rest of the tag source
///
/// Both pieces are trimmed to have no leading or trailing whitespace.
///
/// Returns a TagLexerError when the tag is empty or has an invalid name.
pub fn lex_tag(tag: &str, start: usize) -> Result<Tag, TagLexerError> {
    let rest = tag.trim_start();
    if rest.trim().is_empty() {
        return Err(TagLexerError::EmptyTag {
            at: (
                start - START_TAG_LEN,
                START_TAG_LEN + tag.len() + END_TAG_LEN,
            )
                .into(),
        });
    }

    let start = start + tag.len() - rest.len();
    let tag = rest.trim_end();
    let Some(tag_len) = tag.find(|c: char| !c.is_xid_continue()) else {
        let at = (start, tag.len());
        let parts = TagParts {
            at: (start + tag.len(), 0),
        };
        return Ok(Tag { at, parts });
    };
    let index = tag.next_whitespace();
    if index > tag_len {
        let at = (start, index);
        return Err(TagLexerError::InvalidTagName { at: at.into() });
    }
    let at = (start, tag_len);
    let rest = &tag[tag_len..];
    let trimmed = rest.trim_start();
    let start = start + tag_len + rest.len() - trimmed.len();
    let parts = TagParts {
        at: (start, trimmed.len()),
    };
    Ok(Tag { at, parts })
}

#[cfg(test)]
mod tests {
    use super::*;

    use crate::types::IntoTemplateString;
    use crate::{END_TAG_LEN, START_TAG_LEN};

    fn trim_tag(template: &str) -> &str {
        &template[START_TAG_LEN..(template.len() - END_TAG_LEN)]
    }

    #[test]
    fn test_lex_empty() {
        let template = "{%  %}";
        let tag = trim_tag(template);
        let error = lex_tag(tag, START_TAG_LEN).unwrap_err();
        assert_eq!(error, TagLexerError::EmptyTag { at: (0, 6).into() })
    }

    #[test]
    fn test_lex_tag() {
        let template = "{% csrftoken %}";
        let tag = trim_tag(template);
        let tag = lex_tag(tag, START_TAG_LEN).unwrap();
        assert_eq!(tag.at, (3, 9));
        assert_eq!(tag.content(template.into_template_string()), "csrftoken");
        assert_eq!(tag.parts, TagParts { at: (12, 0) })
    }

    #[test]
    fn test_lex_invalid_tag() {
        let template = "{% url'foo' %}";
        let tag = trim_tag(template);
        let error = lex_tag(tag, START_TAG_LEN).unwrap_err();
        assert_eq!(error, TagLexerError::InvalidTagName { at: (3, 8).into() })
    }

    #[test]
    fn test_lex_invalid_tag_rest() {
        let template = "{% url'foo' bar %}";
        let tag = trim_tag(template);
        let error = lex_tag(tag, START_TAG_LEN).unwrap_err();
        assert_eq!(error, TagLexerError::InvalidTagName { at: (3, 8).into() })
    }

    #[test]
    fn test_lex_tag_rest() {
        let template = "{% url name arg %}";
        let tag = trim_tag(template);
        let tag = lex_tag(tag, START_TAG_LEN).unwrap();
        assert_eq!(tag.at, (3, 3));
        assert_eq!(tag.content(template.into_template_string()), "url");
        assert_eq!(tag.parts, TagParts { at: (7, 8) })
    }

    #[test]
    fn test_template_content_impl() {
        let template = "{% url name arg %}";
        let template_string = "{% url name arg %}".into_template_string();
        let tag = lex_tag(trim_tag(template), START_TAG_LEN).unwrap();
        assert_eq!(tag.content(template.into_template_string()), "url");
        assert_eq!(
            template_string.content(tag.at),
            tag.content(template_string)
        );
        assert_eq!(tag.parts.content(template_string), "name arg");
        assert_eq!(
            template_string.content(tag.parts.at),
            tag.parts.content(template_string)
        );
    }
}
