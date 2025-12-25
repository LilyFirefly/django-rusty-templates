pub mod autoescape;
mod core;
pub mod custom_tag;
pub mod forloop;
pub mod ifcondition;
pub mod load;

use either::{Either, Left, Right};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::TemplateContent;
use crate::tag::OtherTagType::Endblock;
use crate::tag::core::TagLexer;
use crate::types::{At, TemplateString};

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
pub enum StartTagType {
    Autoescape,
    Block,
    Comment,
    CsrfToken,
    Cycle,
    Debug,
    Extends,
    Filter,
    Firstof,
    For,
    Empty,
    If,
    Ifchanged,
    Include,
    Load,
    Lorem,
    Now,
    Partial,
    Partialdef,
    Querystring,
    Regroup,
    Resetcycle,
    Spaceless,
    Templatetag,
    Url,
    Verbatim,
    Widthratio,
    With,
    Custom,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum OtherTagType {
    Endautoescape,
    Endblock,
    Endcomment,
    Endfilter,
    Empty,
    EndFor,
    Elif,
    Else,
    Endif,
    Endifchanged,
    Endpartialdef,
    Endspaceless,
    Endverbatim,
    Endwith,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Tag {
    pub at: At,
    pub tag_type: Either<StartTagType, OtherTagType>,
    pub tag_parts: TagParts,
}

impl Tag {
    fn new(tag_name: &str, at: At, tag_parts: TagParts) -> Tag {
        match tag_name {
            // Simple block tags
            "autoescape" => Tag {
                at,
                tag_type: Left(StartTagType::Autoescape),
                tag_parts,
            },
            "endautoescape" => Tag {
                at,
                tag_type: Right(OtherTagType::Endautoescape),
                tag_parts,
            },
            "csrf_token" => Tag {
                at,
                tag_type: Left(StartTagType::CsrfToken),
                tag_parts,
            },
            "cycle" => Tag {
                at,
                tag_type: Left(StartTagType::Cycle),
                tag_parts,
            },
            "debug" => Tag {
                at,
                tag_type: Left(StartTagType::Debug),
                tag_parts,
            },
            "extends" => Tag {
                at,
                tag_type: Left(StartTagType::Extends),
                tag_parts,
            },
            "firstof" => Tag {
                at,
                tag_type: Left(StartTagType::Firstof),
                tag_parts,
            },
            "include" => Tag {
                at,
                tag_type: Left(StartTagType::Include),
                tag_parts,
            },
            "load" => Tag {
                at,
                tag_type: Left(StartTagType::Load),
                tag_parts,
            },
            "lorem" => Tag {
                at,
                tag_type: Left(StartTagType::Lorem),
                tag_parts,
            },
            "now" => Tag {
                at,
                tag_type: Left(StartTagType::Now),
                tag_parts,
            },
            "partial" => Tag {
                at,
                tag_type: Left(StartTagType::Partial),
                tag_parts,
            },
            "querystring" => Tag {
                at,
                tag_type: Left(StartTagType::Querystring),
                tag_parts,
            },
            "regroup" => Tag {
                at,
                tag_type: Left(StartTagType::Regroup),
                tag_parts,
            },
            "resetcycle" => Tag {
                at,
                tag_type: Left(StartTagType::Resetcycle),
                tag_parts,
            },
            "templatetag" => Tag {
                at,
                tag_type: Left(StartTagType::Templatetag),
                tag_parts,
            },
            "url" => Tag {
                at,
                tag_type: Left(StartTagType::Url),
                tag_parts,
            },
            "widthratio" => Tag {
                at,
                tag_type: Left(StartTagType::Widthratio),
                tag_parts,
            },

            // Complex blocks
            "block" => Tag {
                at,
                tag_type: Left(StartTagType::Block),
                tag_parts,
            },
            "endblock" => Tag {
                at,
                tag_type: Right(Endblock),
                tag_parts,
            },

            "comment" => Tag {
                at,
                tag_type: Left(StartTagType::Comment),
                tag_parts,
            },
            "endcomment" => Tag {
                at,
                tag_type: Right(OtherTagType::Endcomment),
                tag_parts,
            },

            "filter" => Tag {
                at,
                tag_type: Left(StartTagType::Filter),
                tag_parts,
            },
            "endfilter" => Tag {
                at,
                tag_type: Right(OtherTagType::Endfilter),
                tag_parts,
            },

            "for" => Tag {
                at,
                tag_type: Left(StartTagType::For),
                tag_parts,
            },
            "endfor" => Tag {
                at,
                tag_type: Right(OtherTagType::EndFor),
                tag_parts,
            },
            "empty" => Tag {
                at,
                tag_type: Right(OtherTagType::Empty),
                tag_parts,
            },

            "if" => Tag {
                at,
                tag_type: Left(StartTagType::If),
                tag_parts,
            },
            "elif" => Tag {
                at,
                tag_type: Right(OtherTagType::Elif),
                tag_parts,
            },
            "else" => Tag {
                at,
                tag_type: Right(OtherTagType::Else),
                tag_parts,
            },
            "endif" => Tag {
                at,
                tag_type: Right(OtherTagType::Endif),
                tag_parts,
            },

            "ifchanged" => Tag {
                at,
                tag_type: Left(StartTagType::Ifchanged),
                tag_parts,
            },
            "endifchanged" => Tag {
                at,
                tag_type: Right(OtherTagType::Endifchanged),
                tag_parts,
            },

            "partialdef" => Tag {
                at,
                tag_type: Left(StartTagType::Partialdef),
                tag_parts,
            },
            "endpartialdef" => Tag {
                at,
                tag_type: Right(OtherTagType::Endpartialdef),
                tag_parts,
            },

            "spaceless" => Tag {
                at,
                tag_type: Left(StartTagType::Spaceless),
                tag_parts,
            },
            "endspaceless" => Tag {
                at,
                tag_type: Right(OtherTagType::Endspaceless),
                tag_parts,
            },

            "verbatim" => Tag {
                at,
                tag_type: Left(StartTagType::Verbatim),
                tag_parts,
            },
            "endverbatim" => Tag {
                at,
                tag_type: Right(OtherTagType::Endverbatim),
                tag_parts,
            },

            "with" => Tag {
                at,
                tag_type: Left(StartTagType::With),
                tag_parts,
            },
            "endwith" => Tag {
                at,
                tag_type: Right(OtherTagType::Endwith),
                tag_parts,
            },

            // Default case
            _ => Tag {
                at,
                tag_type: Left(StartTagType::Custom),
                tag_parts,
            },
        }
    }
}

impl<'t> TemplateContent<'t> for Tag {
    fn content(&self, template: TemplateString<'t>) -> &'t str {
        template.content(self.at)
    }
}

pub fn lex_tag(tag: &str, start: usize) -> Result<Tag, TagLexerError> {
    TagLexer { tag, start }.lex()
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
        assert_eq!(tag.tag_parts, TagParts { at: (12, 0) })
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
        assert_eq!(tag.tag_parts, TagParts { at: (7, 8) })
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
        assert_eq!(tag.tag_parts.content(template_string), "name arg");
        assert_eq!(
            template_string.content(tag.tag_parts.at),
            tag.tag_parts.content(template_string)
        );
    }
}
