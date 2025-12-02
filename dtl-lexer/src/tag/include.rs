use crate::common::{text_content_at, translated_text_content_at};
use crate::tag::TagParts;
use crate::tag::custom_tag::{SimpleTagLexer, SimpleTagLexerError, SimpleTagTokenType};
use crate::types::{At, TemplateString};

pub struct IncludeTemplateToken {
    pub at: At,
    pub token_type: SimpleTagTokenType,
}

impl IncludeTemplateToken {
    pub fn content_at(&self) -> At {
        match self.token_type {
            SimpleTagTokenType::Variable => self.at,
            SimpleTagTokenType::Numeric => self.at,
            SimpleTagTokenType::Text => text_content_at(self.at),
            SimpleTagTokenType::TranslatedText => translated_text_content_at(self.at),
        }
    }
}

pub struct IncludeLexer<'t>(SimpleTagLexer<'t>);

impl<'t> IncludeLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self(SimpleTagLexer::new(template, parts))
    }

    pub fn lex_template(&mut self) -> Result<IncludeTemplateToken, SimpleTagLexerError> {
        let Some(token) = self.0.next() else { todo!() };
        let token = token?;
        match token.kwarg {
            Some(kwarg_at) => todo!(),
            None => Ok(IncludeTemplateToken {
                at: token.at,
                token_type: token.token_type,
            }),
        }
    }
}
