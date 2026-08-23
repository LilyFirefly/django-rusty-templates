use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::{At, TemplateString};

#[derive(Clone, Debug, PartialEq)]
pub enum CycleArguments {
    Reference {
        name: At,
    },
    Definition {
        values: Vec<TagElementToken>,
        name: Option<At>,
        silent: bool,
    },
}

pub struct CycleLexer<'t> {
    template: TemplateString<'t>,
    lexer: TagElementLexer<'t>,
}

impl<'t> CycleLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            template,
            lexer: TagElementLexer::new(template, parts),
        }
    }

    pub fn tokens(&mut self) -> Result<Vec<TagElementToken>, LexerError> {
        self.lexer.by_ref().collect()
    }

    pub fn lex(mut self) -> Result<Option<CycleArguments>, LexerError> {
        let mut tokens = self.tokens()?;
        match tokens.len() {
            0 => Ok(None),
            1 => Ok(Some(CycleArguments::Reference { name: tokens[0].at })),
            _ => {
                let named_suffix = match tokens.as_slice() {
                    [values @ .., as_token, name_token]
                        if values.len() >= 2 && self.template.content(as_token.at) == "as" =>
                    {
                        Some((values.len(), name_token.at))
                    }
                    _ => None,
                };

                if let Some((value_count, name)) = named_suffix {
                    tokens.truncate(value_count);

                    Ok(Some(CycleArguments::Definition {
                        values: tokens,
                        name: Some(name),
                        silent: false,
                    }))
                } else {
                    Ok(Some(CycleArguments::Definition {
                        values: tokens,
                        name: None,
                        silent: false,
                    }))
                }
            }
        }
    }
}
