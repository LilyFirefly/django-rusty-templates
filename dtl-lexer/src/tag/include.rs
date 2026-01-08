#![expect(unused_assignments)]
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::common::text_content_at;
use crate::tag::TagParts;
use crate::tag::kwarg::{SimpleTagLexer, SimpleTagLexerError, SimpleTagToken, SimpleTagTokenType};
use crate::types::{At, TemplateString};

#[derive(Debug, PartialEq, Eq)]
pub enum IncludeTemplateTokenType {
    Text,
    Variable,
}

#[derive(Debug, PartialEq, Eq)]
pub struct IncludeTemplateToken {
    pub at: At,
    pub token_type: IncludeTemplateTokenType,
}

impl IncludeTemplateToken {
    pub fn content_at(&self) -> At {
        match self.token_type {
            IncludeTemplateTokenType::Variable => self.at,
            IncludeTemplateTokenType::Text => text_content_at(self.at),
        }
    }
}

pub enum IncludeWithToken {
    None,
    With(At),
    Only(At),
}

pub enum IncludeToken {
    Only(At),
    Kwarg { kwarg_at: At, token: SimpleTagToken },
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum IncludeLexerError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    SimpleTagLexerError(#[from] SimpleTagLexerError),
    #[error("Included template name must be a string or iterable of strings.")]
    InvalidTemplateName {
        #[label("invalid template name")]
        at: SourceSpan,
    },
    #[error("Included template name cannot be a translatable string.")]
    TranslatedTemplateName {
        #[label("invalid template name")]
        at: SourceSpan,
    },
    #[error("Unexpected argument")]
    #[diagnostic(help("{help}"))]
    UnexpectedArgument {
        #[label("here")]
        at: SourceSpan,
        help: &'static str,
    },
    #[error("Unexpected keyword argument")]
    UnexpectedKeywordArgument {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Expected a keyword argument")]
    UnexpectedPositionalArgument {
        #[label("here")]
        at: SourceSpan,
    },
}

pub struct IncludeLexer<'t> {
    lexer: SimpleTagLexer<'t>,
    template: TemplateString<'t>,
}

impl<'t> IncludeLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            lexer: SimpleTagLexer::new(template, parts),
            template,
        }
    }

    pub fn lex_template(&mut self) -> Result<Option<IncludeTemplateToken>, IncludeLexerError> {
        let token = match self.lexer.next() {
            Some(token) => token?,
            None => return Ok(None),
        };
        match token.kwarg {
            Some(kwarg_at) => Err(IncludeLexerError::UnexpectedKeywordArgument {
                at: kwarg_at.into(),
            }),
            None => {
                let token_type = match token.token_type {
                    SimpleTagTokenType::Text => IncludeTemplateTokenType::Text,
                    SimpleTagTokenType::Variable => IncludeTemplateTokenType::Variable,
                    SimpleTagTokenType::Numeric => {
                        return Err(IncludeLexerError::InvalidTemplateName {
                            at: token.at.into(),
                        });
                    }
                    SimpleTagTokenType::TranslatedText => {
                        return Err(IncludeLexerError::TranslatedTemplateName {
                            at: token.at.into(),
                        });
                    }
                };
                Ok(Some(IncludeTemplateToken {
                    at: token.at,
                    token_type,
                }))
            }
        }
    }

    fn next_kwarg(&mut self) -> Option<Result<SimpleTagToken, IncludeLexerError>> {
        match self.lexer.next() {
            None => None,
            Some(Ok(token)) => Some(Ok(token)),
            Some(Err(error)) => Some(Err(error.into())),
        }
    }

    fn lex_only(&mut self, at: At) -> Result<IncludeToken, IncludeLexerError> {
        match self.lexer.next() {
            None => Ok(IncludeToken::Only(at)),
            Some(token) => Err(IncludeLexerError::UnexpectedArgument {
                at: token?.all_at().into(),
                help: "Try moving the argument before the 'only' option",
            }),
        }
    }

    pub fn lex_with_or_only(&mut self) -> Result<IncludeWithToken, IncludeLexerError> {
        let token = match self.next_kwarg() {
            None => return Ok(IncludeWithToken::None),
            Some(result) => result?,
        };
        const HELP: &str = "Try adding the 'with' keyword before the argument.";
        match token {
            SimpleTagToken {
                at,
                token_type: SimpleTagTokenType::Variable,
                kwarg: None,
            } => match self.template.content(at) {
                "with" => Ok(IncludeWithToken::With(at)),
                "only" => Ok(IncludeWithToken::Only(at)),
                _ => Err(IncludeLexerError::UnexpectedArgument {
                    at: at.into(),
                    help: HELP,
                }),
            },
            token => Err(IncludeLexerError::UnexpectedArgument {
                at: token.all_at().into(),
                help: HELP,
            }),
        }
    }
}

impl<'t> Iterator for IncludeLexer<'t> {
    type Item = Result<IncludeToken, IncludeLexerError>;

    fn next(&mut self) -> Option<Self::Item> {
        let token = match self.next_kwarg()? {
            Ok(token) => token,
            Err(error) => {
                return Some(Err(error));
            }
        };
        Some(match token.kwarg {
            Some(kwarg_at) => Ok(IncludeToken::Kwarg { kwarg_at, token }),
            None => {
                if token.token_type == SimpleTagTokenType::Variable
                    && self.template.content(token.at) == "only"
                {
                    self.lex_only(token.at)
                } else {
                    Err(IncludeLexerError::UnexpectedPositionalArgument {
                        at: token.at.into(),
                    })
                }
            }
        })
    }
}
