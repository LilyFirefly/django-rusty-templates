use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementToken, TagElementTokenType};
use crate::types::{At, TemplateString};

pub enum FirstOfToken {
    Element(TagElementToken),
    AsVar(At),
}

pub struct FirstOfLexer<'t> {
    template: TemplateString<'t>,
    lexer: TagElementLexer<'t>,
}

impl<'t> FirstOfLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            template,
            lexer: TagElementLexer::new(template, parts),
        }
    }
}

impl<'t> Iterator for FirstOfLexer<'t> {
    type Item = Result<FirstOfToken, LexerError>;

    fn next(&mut self) -> Option<Self::Item> {
        let token = self.lexer.next()?;
        let token = match token {
            Ok(token) => token,
            Err(e) => return Some(Err(e)),
        };

        if token.token_type == TagElementTokenType::Variable {
            let content = self.template.content(token.content_at());
            if content == "as" {
                return Some(Ok(FirstOfToken::AsVar(token.at)));
            }
        }

        Some(Ok(FirstOfToken::Element(token)))
    }
}
