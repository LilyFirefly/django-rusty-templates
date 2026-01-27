use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::TemplateString;

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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::IntoTemplateString;

    #[test]
    fn test_empty_comment() {
        let template = "{% comment %}{% endcomment %}";
        let parts = TagParts { at: (12, 0) };
        let mut lexer = CommentLexer::new(template.into_template_string(), parts);
        assert!(lexer.next().is_none());
    }

    #[test]
    fn test_comment_with_args() {
        let template = "{% comment \"note\" word %}";
        // "quote" (6) + space (1) + word (4) = 11
        let parts = TagParts { at: (11, 11) };
        let lexer = CommentLexer::new(template.into_template_string(), parts);
        let tokens: Vec<_> = lexer.collect::<Result<Vec<_>, _>>().unwrap();
        assert_eq!(tokens.len(), 2);
    }
}
