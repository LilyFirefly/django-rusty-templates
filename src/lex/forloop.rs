use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

use crate::lex::common::{
    LexerError, NextChar, lex_numeric, lex_text, lex_translated, lex_variable,
};
use crate::lex::tag::TagParts;
use crate::types::TemplateString;

#[derive(Clone, Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum ForLexerError {
    #[error(transparent)]
    LexerError(#[from] LexerError),
    #[error("Invalid variable name {name} in for loop:")]
    InvalidName {
        name: String,
        #[label("invalid variable name")]
        at: SourceSpan,
    },
    #[error("Expected an expression after the 'in' keyword:")]
    MissingExpression {
        #[label("after this keyword")]
        at: SourceSpan,
    },
    #[error("Unexpected expression in for loop:")]
    UnexpectedExpression {
        #[label("unexpected expression")]
        at: SourceSpan,
    },
}

#[derive(Clone, Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum ForLexerInError {
    #[error("Unexpected expression in for loop. Did you miss a comma when unpacking?")]
    MissingComma {
        #[label("unexpected expression")]
        at: SourceSpan,
    },
    #[error("Expected the 'in' keyword or a variable name:")]
    MissingIn {
        #[label("after this name")]
        at: SourceSpan,
    },
}

#[derive(Debug, PartialEq, Eq)]
pub enum ForTokenType {
    Numeric,
    Text,
    TranslatedText,
    Variable,
}

#[derive(Debug, PartialEq, Eq)]
pub struct ForVariableNameToken {
    pub at: (usize, usize),
}

#[derive(Debug, PartialEq, Eq)]
pub struct ForVariableToken {
    pub at: (usize, usize),
    pub token_type: ForTokenType,
}

enum State {
    VariableName,
    Done,
}

pub struct ForLexer<'t> {
    rest: &'t str,
    byte: usize,
    state: State,
    previous_at: Option<(usize, usize)>,
}

impl<'t> ForLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            rest: template.content(parts.at),
            byte: parts.at.0,
            state: State::VariableName,
            previous_at: None,
        }
    }

    pub fn lex_expression(&mut self) -> Result<ForVariableToken, ForLexerError> {
        if self.rest.is_empty() {
            return Err(ForLexerError::MissingExpression {
                at: self.previous_at.expect("previous_at is set").into(),
            });
        }
        let mut chars = self.rest.chars();
        let token = match chars.next().expect("self.rest is not empty") {
            '_' => {
                if let Some('(') = chars.next() {
                    self.lex_translated(&mut chars)?
                } else {
                    self.lex_variable()
                }
            }
            '"' => self.lex_text(&mut chars, '"')?,
            '\'' => self.lex_text(&mut chars, '\'')?,
            '0'..='9' | '-' => self.lex_numeric(),
            _ => self.lex_variable(),
        };
        self.lex_remainder()?;
        Ok(token)
    }

    fn lex_variable(&mut self) -> ForVariableToken {
        let (at, byte, rest) = lex_variable(self.byte, self.rest);
        self.rest = rest;
        self.byte = byte;
        ForVariableToken {
            token_type: ForTokenType::Variable,
            at,
        }
    }

    fn lex_numeric(&mut self) -> ForVariableToken {
        let (at, byte, rest) = lex_numeric(self.byte, self.rest);
        self.rest = rest;
        self.byte = byte;
        ForVariableToken {
            at,
            token_type: ForTokenType::Numeric,
        }
    }

    fn lex_text(
        &mut self,
        chars: &mut std::str::Chars,
        end: char,
    ) -> Result<ForVariableToken, ForLexerError> {
        let (at, byte, rest) = lex_text(self.byte, self.rest, chars, end)?;
        self.rest = rest;
        self.byte = byte;
        Ok(ForVariableToken {
            token_type: ForTokenType::Text,
            at,
        })
    }

    fn lex_translated(
        &mut self,
        chars: &mut std::str::Chars,
    ) -> Result<ForVariableToken, ForLexerError> {
        let (at, byte, rest) = lex_translated(self.byte, self.rest, chars)?;
        self.rest = rest;
        self.byte = byte;
        Ok(ForVariableToken {
            token_type: ForTokenType::TranslatedText,
            at,
        })
    }

    fn lex_remainder(&mut self) -> Result<(), ForLexerError> {
        let remainder = self.rest.next_whitespace();
        match remainder {
            0 => {
                let rest = self.rest.trim_start();
                self.byte += self.rest.len() - rest.len();
                self.rest = rest;
                Ok(())
            }
            n => Err(LexerError::InvalidRemainder {
                at: (self.byte, n).into(),
            }
            .into()),
        }
    }

    pub fn lex_in(&mut self) -> Result<(), ForLexerInError> {
        if self.rest.is_empty() {
            return Err(ForLexerInError::MissingIn {
                at: self.previous_at.expect("previous_at is set").into(),
            });
        }
        let index = self.rest.next_whitespace();
        let at = (self.byte, index);
        match &self.rest[..index] {
            "in" => {
                let next_index = self.rest[index..].next_non_whitespace();
                self.byte += index + next_index;
                self.rest = &self.rest[index + next_index..];
                self.previous_at = Some(at);
                Ok(())
            }
            _ => Err(ForLexerInError::MissingComma { at: at.into() }),
        }
    }

    pub fn lex_reversed(&mut self) -> Result<bool, ForLexerError> {
        if self.rest.is_empty() {
            return Ok(false);
        }
        let index = self.rest.next_whitespace();
        let at = match &self.rest[..index] {
            "reversed" => {
                let next_index = self.rest[index..].next_non_whitespace();
                match self.rest[index + next_index..].len() {
                    0 => return Ok(true),
                    len => (self.byte + index + next_index, len),
                }
            }
            _ => (self.byte, index),
        };
        Err(ForLexerError::UnexpectedExpression { at: at.into() })
    }

    pub fn lex_variable_name(&mut self) -> Option<Result<ForVariableNameToken, ForLexerError>> {
        match self.state {
            State::VariableName if !self.rest.is_empty() => {}
            State::VariableName => {
                self.state = State::Done;
                return None;
            }
            State::Done => return None,
        }
        let index = self.rest.next_whitespace();
        let (index, next_index) = match self.rest.find(',') {
            Some(comma_index) if comma_index < index => {
                let next_index = self.rest[comma_index + 1..].next_non_whitespace();
                (comma_index, next_index + 1)
            }
            _ => {
                self.state = State::Done;
                let next_index = self.rest[index..].next_non_whitespace();
                (index, next_index)
            }
        };
        let at = (self.byte, index);
        self.previous_at = Some(at);
        let name = &self.rest[..index];
        if name.contains(['"', '\'', '|']) {
            self.rest = "";
            self.state = State::Done;
            return Some(Err(ForLexerError::InvalidName {
                name: name.to_string(),
                at: at.into(),
            }));
        }
        self.byte += index + next_index;
        self.rest = &self.rest[index + next_index..];
        Some(Ok(ForVariableNameToken { at }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lex_simple() {
        let template = "{% for foo in bar %}";
        let parts = TagParts { at: (7, 10) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 3),
            token_type: ForTokenType::Variable,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_text() {
        let template = "{% for foo in 'bar' %}";
        let parts = TagParts { at: (7, 12) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 5),
            token_type: ForTokenType::Text,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_text_double_quotes() {
        let template = "{% for foo in \"bar\" %}";
        let parts = TagParts { at: (7, 12) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 5),
            token_type: ForTokenType::Text,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_translated_text() {
        let template = "{% for foo in _('bar') %}";
        let parts = TagParts { at: (7, 15) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 8),
            token_type: ForTokenType::TranslatedText,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_underscore_expression() {
        let template = "{% for foo in _bar %}";
        let parts = TagParts { at: (7, 11) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 4),
            token_type: ForTokenType::Variable,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_int() {
        let template = "{% for foo in 123 %}";
        let parts = TagParts { at: (7, 10) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 3),
            token_type: ForTokenType::Numeric,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_variable_names() {
        let template = "{% for foo, bar in spam %}";
        let parts = TagParts { at: (7, 16) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableNameToken { at: (12, 3) };
        let spam = ForVariableToken {
            at: (19, 4),
            token_type: ForTokenType::Variable,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), bar);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), spam);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_variable_names_no_whitespace_after_comma() {
        let template = "{% for foo,bar in spam %}";
        let parts = TagParts { at: (7, 15) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableNameToken { at: (11, 3) };
        let spam = ForVariableToken {
            at: (18, 4),
            token_type: ForTokenType::Variable,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), bar);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), spam);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_comma_in_text() {
        let template = "{% for foo in 'spam,' %}";
        let parts = TagParts { at: (7, 14) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let spam = ForVariableToken {
            at: (14, 7),
            token_type: ForTokenType::Text,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), spam);
        assert!(!lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_lex_reversed() {
        let template = "{% for foo in bar reversed %}";
        let parts = TagParts { at: (7, 19) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 3),
            token_type: ForTokenType::Variable,
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert!(lexer.lex_reversed().unwrap());
    }

    #[test]
    fn test_unexpected_before_in() {
        let template = "{% for foo bar in bar reversed %}";
        let parts = TagParts { at: (7, 23) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let unexpected = ForLexerInError::MissingComma { at: (11, 3).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        assert_eq!(lexer.lex_in().unwrap_err(), unexpected);
    }

    #[test]
    fn test_unexpected_after_iterable() {
        let template = "{% for foo in bar invalid %}";
        let parts = TagParts { at: (7, 18) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 3),
            token_type: ForTokenType::Variable,
        };
        let unexpected = ForLexerError::UnexpectedExpression { at: (18, 7).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert_eq!(lexer.lex_reversed().unwrap_err(), unexpected);
    }

    #[test]
    fn test_unexpected_after_reversed() {
        let template = "{% for foo in bar reversed invalid %}";
        let parts = TagParts { at: (7, 27) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let bar = ForVariableToken {
            at: (14, 3),
            token_type: ForTokenType::Variable,
        };
        let unexpected = ForLexerError::UnexpectedExpression { at: (27, 7).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap(), bar);
        assert_eq!(lexer.lex_reversed().unwrap_err(), unexpected);
    }

    #[test]
    fn test_incomplete_string() {
        let template = "{% for foo in 'bar %}";
        let parts = TagParts { at: (7, 11) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let incomplete = LexerError::IncompleteString { at: (14, 4).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap_err(), incomplete.into());
    }

    #[test]
    fn test_incomplete_translated_string() {
        let template = "{% for foo in _('bar' %}";
        let parts = TagParts { at: (7, 14) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let incomplete = LexerError::IncompleteTranslatedString { at: (14, 7).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap_err(), incomplete.into());
    }

    #[test]
    fn test_invalid_remainder() {
        let template = "{% for foo in 'bar'baz %}";
        let parts = TagParts { at: (7, 15) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let foo = ForVariableNameToken { at: (7, 3) };
        let incomplete = LexerError::InvalidRemainder { at: (19, 3).into() };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap(), foo);
        lexer.lex_in().unwrap();
        assert_eq!(lexer.lex_expression().unwrap_err(), incomplete.into());
    }

    #[test]
    fn test_invalid_name() {
        let template = "{% for '2' in 'bar' %}";
        let parts = TagParts { at: (7, 12) };
        let mut lexer = ForLexer::new(template.into(), parts);

        let invalid = ForLexerError::InvalidName {
            name: "'2'".to_string(),
            at: (7, 3).into(),
        };
        assert_eq!(lexer.lex_variable_name().unwrap().unwrap_err(), invalid);
    }
}
