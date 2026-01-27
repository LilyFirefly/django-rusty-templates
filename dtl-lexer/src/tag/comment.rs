use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::TemplateString;
use crate::tag::TagParts;
use crate::common::LexerError;

pub struct CommentLexer<'t> {
    lexer: TagElementLexer<'t>,
}

impl<'t> CommentLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            lexer: TagElementLexer::new(template, parts),
        }
    }
}

impl<'t> Iterator for CommentLexer<'t> {
    type Item = Result<TagElementToken, LexerError>;

    fn next(&mut self) -> Option<Self::Item> {
        self.lexer.next()
    }
}
