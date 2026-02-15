#![expect(unused_assignments)]
use crate::common::LexerError;
use crate::tag::TagParts;
use crate::tag::common::TagElementTokenType::Variable;
use crate::tag::common::{TagElementLexer, TagElementToken};
use crate::types::{At, TemplateString};
use miette::{Diagnostic, SourceSpan};
use thiserror::Error;

pub struct NowLexer<'t> {
    template: TemplateString<'t>,
    lexer: TagElementLexer<'t>,
    parts: TagParts,
}

impl<'t> NowLexer<'t> {
    pub fn new(template: TemplateString<'t>, parts: TagParts) -> Self {
        Self {
            template,
            lexer: TagElementLexer::new(template, parts.clone()),
            parts,
        }
    }

    fn next_element(&mut self) -> Result<Option<TagElementToken>, NowError> {
        self.lexer.next().transpose().or_else(|err| match err {
            LexerError::IncompleteString { at }
            | LexerError::IncompleteTranslatedString { at }
            | LexerError::InvalidVariableName { at }
            | LexerError::MissingTranslatedString { at } => Ok(Some(TagElementToken {
                at: (at.offset(), at.len()),
                token_type: Variable,
            })),
            // TODO: Django's tokenizer does not treats {% now "Y"invalid %} as lexical error.
            //       We match this behavior here for compatibility, but this should be reverted to a strict LexerError
            //       if Django's parser becomes more strict in the future.
            LexerError::InvalidRemainder { at, .. } => {
                let start_of_tag = self.parts.at.0;
                let end_of_junk = at.offset() + at.len();

                let total_len = end_of_junk - start_of_tag;

                Ok(Some(TagElementToken {
                    at: (start_of_tag, total_len),
                    token_type: Variable,
                }))
            }
        })
    }

    pub fn lex_format(&mut self) -> Result<At, NowError> {
        let Some(token) = self.next_element()? else {
            return Err(NowError::MissingFormat {
                at: self.parts.at.into(),
            });
        };
        Ok(token.at)
    }

    pub fn lex_variable(&mut self) -> Result<Option<At>, NowError> {
        let Some(token) = self.next_element()? else {
            return Ok(None);
        };

        match self.template.content(token.at) {
            "as" => {
                let Some(var) = self.next_element()? else {
                    let position_after_as = token.at.0 + token.at.1;
                    return Err(NowError::MissingVariableAfterAs {
                        at: SourceSpan::new(position_after_as.into(), 0usize),
                    });
                };

                Ok(Some(var.at))
            }
            _ => Err(NowError::UnexpectedAfterFormat {
                at: token.at.into(),
            }),
        }
    }

    pub fn extra_token(&mut self) -> Result<Option<TagElementToken>, NowError> {
        match self.next_element()? {
            None => Ok(None),
            Some(token) => Err(NowError::UnexpectedAfterVariable {
                at: token.at.into(),
            }),
        }
    }
}

#[derive(Debug, Diagnostic, Error, PartialEq, Eq)]
pub enum NowError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),

    #[error("Unexpected argument after format string")]
    #[diagnostic(help("If you want to store the result in a variable, use the 'as' keyword."))]
    UnexpectedAfterFormat {
        #[label("unexpected argument")]
        at: SourceSpan,
    },

    #[error("Expected a variable name after 'as'")]
    #[diagnostic(help("Provide a name to store the date string, e.g. 'as my_var'"))]
    MissingVariableAfterAs {
        #[label("expected a variable name here")]
        at: SourceSpan,
    },

    #[error("Unexpected argument after variable name")]
    #[diagnostic(help(
        "The 'now' tag only accepts one variable assignment. Try removing this extra argument."
    ))]
    UnexpectedAfterVariable {
        #[label("extra argument")]
        at: SourceSpan,
    },

    #[error("Expected a format string")]
    #[diagnostic(help(
        "The 'now' tag requires a format string, like \"Y-m-d\" or \"DATE_FORMAT\"."
    ))]
    MissingFormat {
        #[label("missing format")]
        at: SourceSpan,
    },
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::IntoTemplateString;

    #[test]
    fn test_lex_format_success() {
        let template = r#"{% now "Y-m-d" %}"#;
        let parts = TagParts { at: (7, 7) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        assert_eq!(lexer.lex_format().unwrap(), (7, 7));
    }

    #[test]
    fn test_lex_format_incomplete_string() {
        let template = r#"{% now "Y-m-d %}"#;
        let parts = TagParts { at: (7, 6) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        assert_eq!(lexer.lex_format().unwrap(), (7, 6));
    }

    #[test]
    fn test_lex_format_missing() {
        let template = r#"{% now %}"#;
        let parts = TagParts { at: (7, 0) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        assert!(matches!(
            lexer.lex_format(),
            Err(NowError::MissingFormat { .. })
        ));
    }

    #[test]
    fn test_lex_variable_as_success() {
        let template = r#"{% now "Y" as current_year %}"#;
        let parts = TagParts { at: (7, 19) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        assert_eq!(lexer.lex_variable().unwrap(), Some((14, 12)));
    }

    #[test]
    fn test_lex_variable_missing_after_as() {
        let template = r#"{% now "Y" as %}"#;
        let parts = TagParts { at: (7, 6) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        assert!(matches!(
            lexer.lex_variable(),
            Err(NowError::MissingVariableAfterAs { .. })
        ));
    }

    #[test]
    fn test_lex_extra_token_error() {
        let template = r#"{% now "Y" as x y %}"#;
        let parts = TagParts { at: (7, 10) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        lexer.lex_variable().unwrap();
        assert!(matches!(
            lexer.extra_token(),
            Err(NowError::UnexpectedAfterVariable { .. })
        ));
    }

    #[test]
    fn test_lex_format_invalid_remainder() {
        let template = r#"{% now "Y"invalid %}"#;
        let parts = TagParts { at: (7, 10) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        // "Y" is (7, 3), invalid starts at 10.
        // next_element should return everything from start_of_tag (7) to end of junk.
        assert_eq!(lexer.lex_format().unwrap(), (7, 10));
    }

    #[test]
    fn test_lex_format_incomplete_translated_string() {
        let template = r#"{% now _("Y") %}"#;
        let parts = TagParts { at: (7, 5) }; // _("Y"
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        assert_eq!(lexer.lex_format().unwrap(), (7, 5));
    }

    #[test]
    fn test_lex_format_missing_translated_string() {
        let template = r#"{% now _() %}"#;
        let parts = TagParts { at: (7, 3) }; // _()
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        assert_eq!(lexer.lex_format().unwrap(), (7, 3));
    }

    #[test]
    fn test_lex_variable_none() {
        let template = r#"{% now "Y" %}"#;
        let parts = TagParts { at: (7, 3) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        assert_eq!(lexer.lex_variable().unwrap(), None);
    }

    #[test]
    fn test_lex_variable_unexpected_after_format() {
        let template = r#"{% now "Y" "junk" %}"#;
        let parts = TagParts { at: (7, 10) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        assert!(matches!(
            lexer.lex_variable(),
            Err(NowError::UnexpectedAfterFormat { .. })
        ));
    }

    #[test]
    fn test_extra_token_none() {
        let template = r#"{% now "Y" as var %}"#;
        let parts = TagParts { at: (7, 10) };
        let mut lexer = NowLexer::new(template.into_template_string(), parts);
        lexer.lex_format().unwrap();
        lexer.lex_variable().unwrap();
        assert_eq!(lexer.extra_token().unwrap(), None);
    }
}
