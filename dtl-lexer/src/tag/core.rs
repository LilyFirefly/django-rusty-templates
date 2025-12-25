use crate::common::NextChar;
use crate::tag::{Tag, TagLexerError, TagParts};
use crate::types::At;
use crate::{END_TAG_LEN, START_TAG_LEN};
use unicode_xid::UnicodeXID;

pub(super) struct TagLexer<'t> {
    pub(super) tag: &'t str,
    pub(super) start: usize,
}

impl<'t> TagLexer<'t> {
    pub(super) fn lex(&self) -> Result<Tag, TagLexerError> {
        let rest = self.tag.trim_start();
        if rest.trim().is_empty() {
            return Err(TagLexerError::EmptyTag {
                at: (
                    self.start - START_TAG_LEN,
                    START_TAG_LEN + self.tag.len() + END_TAG_LEN,
                )
                    .into(),
            });
        }

        let start = self.start + self.tag.len() - rest.len();
        let tag = self.tag.trim();
        let Some(tag_len) = tag.find(|c: char| !c.is_xid_continue()) else {
            let at = (start, tag.len());
            let parts = TagParts {
                at: (start + tag.len(), 0),
            };
            return Ok(Tag::new(self.span(at), at, parts));
        };
        let index = tag.next_whitespace();
        if index > tag_len {
            let at = (start, index);
            return Err(TagLexerError::InvalidTagName { at: at.into() });
        }
        let at = (start, tag_len);
        let rest = &tag[tag_len..];
        let trimmed = rest.trim();
        let start = start + tag_len + rest.len() - trimmed.len();
        let parts = TagParts {
            at: (start, trimmed.len()),
        };
        Ok(Tag::new(self.span(at), at, parts))
    }

    fn span(&self, at: At) -> &'t str {
        let local_start = at.0 - self.start;
        let local_end = local_start + at.1;
        &self.tag[local_start..local_end]
    }
}
