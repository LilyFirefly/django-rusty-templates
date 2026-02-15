// Silence lint warnings for Miette Diagnostic
// https://github.com/zkat/miette/issues/458
// https://github.com/rust-lang/rust/issues/147648
#![expect(unused_assignments)]
use dtl_lexer::DelimitedToken;
use std::borrow::Cow;
use std::collections::{HashMap, HashSet};
use std::iter::Peekable;
use std::sync::Arc;

use either::Either;
use miette::{Diagnostic, SourceSpan};
use num_bigint::BigInt;
use pyo3::intern;
use pyo3::prelude::*;
use thiserror::Error;

use crate::filters::AddFilter;
use crate::filters::AddSlashesFilter;
use crate::filters::CapfirstFilter;
use crate::filters::CenterFilter;
use crate::filters::CutFilter;
use crate::filters::DateFilter;
use crate::filters::DefaultFilter;
use crate::filters::DefaultIfNoneFilter;
use crate::filters::EscapeFilter;
use crate::filters::EscapejsFilter;
use crate::filters::ExternalFilter;
use crate::filters::FilterType;
use crate::filters::LengthFilter;
use crate::filters::LowerFilter;
use crate::filters::SafeFilter;
use crate::filters::SlugifyFilter;
use crate::filters::TitleFilter;
use crate::filters::UpperFilter;
use crate::filters::WordcountFilter;
use crate::filters::WordwrapFilter;
use crate::filters::YesnoFilter;
use dtl_lexer::common::{LexerError, get_all_at, text_content_at, translated_text_content_at};
use dtl_lexer::core::{Lexer, TokenType};
use dtl_lexer::tag::autoescape::{AutoescapeEnabled, AutoescapeError, lex_autoescape_argument};
use dtl_lexer::tag::common::{TagElementToken, TagElementTokenType};
use dtl_lexer::tag::forloop::{ForLexer, ForLexerError, ForLexerInError, ForTokenType};
use dtl_lexer::tag::ifcondition::{
    IfConditionAtom, IfConditionLexer, IfConditionOperator, IfConditionTokenType,
};
use dtl_lexer::tag::include::{
    IncludeLexer, IncludeLexerError, IncludeTemplateToken, IncludeTemplateTokenType, IncludeToken,
    IncludeWithToken,
};
use dtl_lexer::tag::kwarg::{
    TagElementKwargLexer, TagElementKwargLexerError, TagElementKwargToken,
};
use dtl_lexer::tag::load::{LoadLexer, LoadToken};
use dtl_lexer::tag::lorem::{LoremError, LoremLexer, LoremMethod, LoremTokenType};
use dtl_lexer::tag::now::{NowError, NowLexer};
use dtl_lexer::tag::templatetag::{TemplateTag, TemplateTagError, lex_templatetag};
use dtl_lexer::tag::{TagLexerError, TagParts, lex_tag};
use dtl_lexer::types::{At, TemplateString};
use dtl_lexer::variable::{
    Argument as ArgumentToken, VariableLexerError, VariableToken, lex_variable_or_filter,
};
use dtl_lexer::{START_TAG_LEN, TemplateContent};

use crate::path::{RelativePathError, construct_relative_path};
use crate::template::django_rusty_templates::Engine;
use crate::types::Argument;
use crate::types::ArgumentType;
use crate::types::ForVariable;
use crate::types::ForVariableName;

use crate::types::Text;
use crate::types::TranslatedText;
use dtl_lexer::types::Variable;

trait Parse<R> {
    fn parse(&self, parser: &Parser) -> Result<R, ParseError>;
}
#[derive(Debug, Clone, PartialEq)]
pub struct Lorem {
    pub count: TagElement,
    pub method: LoremMethod,
    pub common: bool,
}

#[derive(Debug, PartialEq, Clone)]
pub struct Comment;

#[derive(Debug, PartialEq, Clone)]
pub struct CsrfToken;

impl Parse<Argument> for ArgumentToken {
    fn parse(&self, parser: &Parser) -> Result<Argument, ParseError> {
        Ok(match *self {
            Self::Variable(at) => Argument {
                at,
                argument_type: parser.parse_for_variable(at).into(),
            },
            Self::Text(at) => Argument {
                at,
                argument_type: ArgumentType::Text(Text::new(self.content_at())),
            },
            Self::TranslatedText(at) => Argument {
                at,
                argument_type: ArgumentType::TranslatedText(TranslatedText::new(self.content_at())),
            },
            Self::Numeric(at) => {
                let content = parser.template.content(at);
                let argument_type = match content.parse::<BigInt>() {
                    Ok(n) => ArgumentType::Int(n),
                    Err(_) => match content.parse::<f64>() {
                        Ok(f) => ArgumentType::Float(f),
                        Err(_) => return Err(ParseError::InvalidNumber { at: at.into() }),
                    },
                };
                Argument { at, argument_type }
            }
        })
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum TagElement {
    Int(BigInt),
    Float(f64),
    Text(Text),
    TranslatedText(Text),
    Variable(Variable),
    ForVariable(ForVariable),
    Filter(Box<Filter>),
}

fn unexpected_argument(filter: &'static str, right: Argument) -> ParseError {
    ParseError::UnexpectedArgument {
        filter,
        at: right.at.into(),
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Filter {
    pub at: At,
    pub all_at: At,
    pub left: TagElement,
    pub filter: FilterType,
}

impl Filter {
    pub fn new(
        parser: &Parser,
        at: At,
        all_at: At,
        left: TagElement,
        right: Option<Argument>,
    ) -> Result<Self, ParseError> {
        let filter = match parser.template.content(at) {
            "add" => match right {
                Some(right) => FilterType::Add(AddFilter::new(right)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "addslashes" => match right {
                Some(right) => return Err(unexpected_argument("addslashes", right)),
                None => FilterType::AddSlashes(AddSlashesFilter),
            },
            "capfirst" => match right {
                Some(right) => return Err(unexpected_argument("capfirst", right)),
                None => FilterType::Capfirst(CapfirstFilter),
            },
            "center" => match right {
                Some(right) => FilterType::Center(CenterFilter::new(right)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "cut" => match right {
                Some(right) => FilterType::Cut(CutFilter::new(right)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "default" => match right {
                Some(right) => FilterType::Default(DefaultFilter::new(right, at)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "default_if_none" => match right {
                Some(right) => FilterType::DefaultIfNone(DefaultIfNoneFilter::new(right)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "date" => FilterType::Date(DateFilter::new(right, at)),
            "escape" => match right {
                Some(right) => return Err(unexpected_argument("escape", right)),
                None => FilterType::Escape(EscapeFilter),
            },
            "escapejs" => match right {
                Some(right) => return Err(unexpected_argument("escapejs", right)),
                None => FilterType::Escapejs(EscapejsFilter),
            },
            "lower" => match right {
                Some(right) => return Err(unexpected_argument("lower", right)),
                None => FilterType::Lower(LowerFilter),
            },
            "length" => match right {
                Some(right) => return Err(unexpected_argument("length", right)),
                None => FilterType::Length(LengthFilter),
            },
            "safe" => match right {
                Some(right) => return Err(unexpected_argument("safe", right)),
                None => FilterType::Safe(SafeFilter),
            },
            "slugify" => match right {
                Some(right) => return Err(unexpected_argument("slugify", right)),
                None => FilterType::Slugify(SlugifyFilter),
            },
            "title" => match right {
                Some(right) => return Err(unexpected_argument("title", right)),
                None => FilterType::Title(TitleFilter),
            },
            "upper" => match right {
                Some(right) => return Err(unexpected_argument("upper", right)),
                None => FilterType::Upper(UpperFilter),
            },
            "wordcount" => match right {
                Some(right) => return Err(unexpected_argument("wordcount", right)),
                None => FilterType::Wordcount(WordcountFilter),
            },
            "wordwrap" => match right {
                Some(right) => FilterType::Wordwrap(WordwrapFilter::new(right)),
                None => return Err(ParseError::MissingArgument { at: at.into() }),
            },
            "yesno" => FilterType::Yesno(YesnoFilter::new(at, right)),
            external => {
                let external = match parser.external_filters.get(external) {
                    Some(external) => external.clone().unbind(),
                    None => {
                        return Err(ParseError::InvalidFilter {
                            at: at.into(),
                            filter: external.to_string(),
                        });
                    }
                };
                FilterType::External(ExternalFilter::new(external, right))
            }
        };
        Ok(Self {
            at,
            all_at,
            left,
            filter,
        })
    }
}

fn parse_numeric(content: &str, at: At) -> Result<TagElement, ParseError> {
    match content.parse::<BigInt>() {
        Ok(n) => Ok(TagElement::Int(n)),
        Err(_) => match content.parse::<f64>() {
            Ok(f) => Ok(TagElement::Float(f)),
            Err(_) => Err(ParseError::InvalidNumber { at: at.into() }),
        },
    }
}

impl Parse<TagElement> for TagElementToken {
    fn parse(&self, parser: &Parser) -> Result<TagElement, ParseError> {
        let content_at = self.content_at();
        let (start, _len) = content_at;
        let content = parser.template.content(content_at);
        match self.token_type {
            TagElementTokenType::Numeric => parse_numeric(content, self.at),
            TagElementTokenType::Text => Ok(TagElement::Text(Text::new(content_at))),
            TagElementTokenType::TranslatedText => {
                Ok(TagElement::TranslatedText(Text::new(content_at)))
            }
            TagElementTokenType::Variable => parser.parse_variable(content, content_at, start),
        }
    }
}

impl Parse<TagElement> for TagElementKwargToken {
    fn parse(&self, parser: &Parser) -> Result<TagElement, ParseError> {
        let content_at = self.content_at();
        let (start, _len) = content_at;
        let content = parser.template.content(content_at);
        match self.token_type {
            TagElementTokenType::Numeric => parse_numeric(content, self.at),
            TagElementTokenType::Text => Ok(TagElement::Text(Text::new(content_at))),
            TagElementTokenType::TranslatedText => {
                Ok(TagElement::TranslatedText(Text::new(content_at)))
            }
            TagElementTokenType::Variable => parser.parse_variable(content, content_at, start),
        }
    }
}

/// Extracts "as variable" from the end of the tokens list (and truncates it).
///
/// This will return:
/// - Ok(Some(variable_name)) if found and valid
/// - Ok(None) if "as" not found
/// - ParseError if as is not at the end or missing a variable
fn extract_as_variable(
    tokens: &mut Vec<TagElementKwargToken>,
    template: &TemplateString<'_>,
) -> Result<Option<String>, ParseError> {
    let len = tokens.len();
    if len < 2 {
        return Ok(None);
    }
    for (idx, token) in tokens.iter().rev().enumerate() {
        if template.content(token.at) == "as" {
            println!("{:?}", token.at);
            return match idx {
                0 => Err(ParseError::MissingVariableAfterAs {
                    at: token.at.into(),
                }),
                1 => {
                    let variable = template.content(tokens[len - 1].at).to_string();
                    tokens.truncate(len - 2);
                    Ok(Some(variable))
                }
                _ => Err(ParseError::UnexpectedTokensAfterAsVariable {
                    at: get_all_at(tokens[len - idx + 1].at, tokens[len - 1].at).into(),
                }),
            };
        }
    }
    Ok(None)
}

fn parse_include_template_token(
    token: IncludeTemplateToken,
    parser: &Parser,
) -> Result<IncludeTemplateName, ParseError> {
    let content_at = token.content_at();
    let (start, _len) = content_at;
    let content = parser.template.content(content_at);
    Ok(match token.token_type {
        IncludeTemplateTokenType::Text => IncludeTemplateName::Text(Text::new(content_at)),
        IncludeTemplateTokenType::Variable => {
            IncludeTemplateName::Variable(parser.parse_variable(content, content_at, start)?)
        }
    })
}

#[derive(Clone, Debug, PartialEq)]
pub struct Url {
    pub view_name: TagElement,
    pub args: Vec<TagElement>,
    pub kwargs: Vec<(String, TagElement)>,
    pub asvar: Option<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum IfCondition {
    Variable(TagElement),
    And(Box<(Self, Self)>),
    Or(Box<(Self, Self)>),
    Not(Box<Self>),
    Equal(Box<(Self, Self)>),
    NotEqual(Box<(Self, Self)>),
    LessThan(Box<(Self, Self)>),
    GreaterThan(Box<(Self, Self)>),
    LessThanEqual(Box<(Self, Self)>),
    GreaterThanEqual(Box<(Self, Self)>),
    In(Box<(Self, Self)>),
    NotIn(Box<(Self, Self)>),
    Is(Box<(Self, Self)>),
    IsNot(Box<(Self, Self)>),
}

fn parse_if_condition(
    parser: &mut Parser,
    parts: TagParts,
    at: At,
) -> Result<IfCondition, ParseError> {
    let mut lexer = IfConditionLexer::new(parser.template, parts).peekable();
    if lexer.peek().is_none() {
        return Err(ParseError::MissingBooleanExpression { at: at.into() });
    }
    parse_if_binding_power(parser, &mut lexer, 0, at)
}

fn parse_if_binding_power(
    parser: &mut Parser,
    lexer: &mut Peekable<IfConditionLexer>,
    min_binding_power: u8,
    at: At,
) -> Result<IfCondition, ParseError> {
    let Some(token) = lexer.next().transpose()? else {
        return Err(ParseError::UnexpectedEndExpression { at: at.into() });
    };
    let content = token.content(parser.template);
    let token_at = token.content_at();
    let mut lhs = match token.token_type {
        IfConditionTokenType::Atom(IfConditionAtom::Numeric) => {
            IfCondition::Variable(parse_numeric(content, token_at)?)
        }
        IfConditionTokenType::Atom(IfConditionAtom::Text) => {
            IfCondition::Variable(TagElement::Text(Text::new(token_at)))
        }
        IfConditionTokenType::Atom(IfConditionAtom::TranslatedText) => {
            IfCondition::Variable(TagElement::TranslatedText(Text::new(token_at)))
        }
        IfConditionTokenType::Atom(IfConditionAtom::Variable) => {
            IfCondition::Variable(parser.parse_variable(content, token_at, token.at.0)?)
        }
        IfConditionTokenType::Not => {
            let if_condition = parse_if_binding_power(parser, lexer, NOT_BINDING_POWER, token_at)?;
            IfCondition::Not(Box::new(if_condition))
        }
        _ => {
            return Err(ParseError::InvalidIfPosition {
                at: token.at.into(),
                token: content.to_string(),
            });
        }
    };

    loop {
        let token = match lexer.peek() {
            None => break,
            Some(Err(e)) => return Err(e.clone().into()),
            Some(Ok(token)) => token,
        };
        let operator = match &token.token_type {
            IfConditionTokenType::Atom(_) | IfConditionTokenType::Not => {
                return Err(ParseError::UnusedExpression {
                    at: token.at.into(),
                    expression: parser.template.content(token.at).to_string(),
                });
            }
            IfConditionTokenType::Operator(operator) => *operator,
        };
        let binding_power = operator.binding_power();
        if binding_power <= min_binding_power {
            break;
        }

        // We can get the next token properly now, since we have the right binding
        // power and don't need to `break`.
        let token = lexer
            .next()
            .expect("already `break`ed in match peek()")
            .expect("already `return Err` in match peek()");
        let rhs = parse_if_binding_power(parser, lexer, binding_power, token.at)?;

        lhs = operator.build_condition(lhs, rhs);
    }

    Ok(lhs)
}

const NOT_BINDING_POWER: u8 = 8;

trait IfConditionOperatorMethods {
    fn binding_power(&self) -> u8;
    fn build_condition(&self, lhs: IfCondition, rhs: IfCondition) -> IfCondition;
}

impl IfConditionOperatorMethods for IfConditionOperator {
    fn binding_power(&self) -> u8 {
        match self {
            Self::Or => 6,
            Self::And => 7,
            Self::In | Self::NotIn => 9,
            Self::Is
            | Self::IsNot
            | Self::Equal
            | Self::NotEqual
            | Self::GreaterThan
            | Self::GreaterThanEqual
            | Self::LessThan
            | Self::LessThanEqual => 10,
        }
    }

    fn build_condition(&self, lhs: IfCondition, rhs: IfCondition) -> IfCondition {
        let inner = Box::new((lhs, rhs));
        match self {
            Self::And => IfCondition::And(inner),
            Self::Or => IfCondition::Or(inner),
            Self::In => IfCondition::In(inner),
            Self::NotIn => IfCondition::NotIn(inner),
            Self::Is => IfCondition::Is(inner),
            Self::IsNot => IfCondition::IsNot(inner),
            Self::Equal => IfCondition::Equal(inner),
            Self::NotEqual => IfCondition::NotEqual(inner),
            Self::GreaterThan => IfCondition::GreaterThan(inner),
            Self::GreaterThanEqual => IfCondition::GreaterThanEqual(inner),
            Self::LessThan => IfCondition::LessThan(inner),
            Self::LessThanEqual => IfCondition::LessThanEqual(inner),
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct ForIterable {
    pub iterable: TagElement,
    pub at: At,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ForNames {
    pub names: Vec<String>,
    pub at: At,
}

fn parse_for_loop(
    parser: &mut Parser,
    parts: TagParts,
    at: At,
) -> Result<(ForIterable, ForNames, bool), ParseError> {
    let mut lexer = ForLexer::new(parser.template, parts);
    let mut variable_names = Vec::new();
    while let Some(token) = lexer.lex_variable_name() {
        variable_names.push(token?);
    }
    if variable_names.is_empty() {
        return Err(ForParseError::MissingVariableNames { at: at.into() }.into());
    }
    let variables_start = variable_names[0].at.0;
    let last = variable_names
        .last()
        .expect("Variables has at least one element");
    let variables_at = (variables_start, last.at.0 - variables_start + last.at.1);

    if let Err(error) = lexer.lex_in() {
        if parser.template.content(last.at) != "in" {
            return Err(error.into());
        }
        let len = variable_names.len();
        match error {
            ForLexerInError::MissingComma { .. } if len >= 2 => {
                let previous = &variable_names[len - 2];
                let at = previous.at.into();
                return Err(ForParseError::MissingVariable { at }.into());
            }
            _ => {
                let at = last.at.into();
                return Err(ForParseError::MissingVariableBeforeIn { at }.into());
            }
        }
    }

    let expression_token = lexer.lex_expression()?;
    let reversed = lexer.lex_reversed()?;
    let variable_names = variable_names
        .iter()
        .map(|token| parser.template.content(token.at).to_string())
        .collect();
    let expression_content = parser.template.content(expression_token.at);
    let expression = match expression_token.token_type {
        ForTokenType::Numeric => {
            return Err(ParseError::NotIterable {
                literal: expression_content.to_string(),
                at: expression_token.at.into(),
            });
        }
        ForTokenType::Text => TagElement::Text(Text::new(text_content_at(expression_token.at))),
        ForTokenType::TranslatedText => {
            TagElement::TranslatedText(Text::new(translated_text_content_at(expression_token.at)))
        }
        ForTokenType::Variable => parser.parse_variable(
            expression_content,
            expression_token.at,
            expression_token.at.0,
        )?,
    };
    Ok((
        ForIterable {
            iterable: expression,
            at: expression_token.at,
        },
        ForNames {
            names: variable_names,
            at: variables_at,
        },
        reversed,
    ))
}

#[derive(Clone, Debug, PartialEq)]
pub struct For {
    pub iterable: ForIterable,
    pub variables: ForNames,
    pub reversed: bool,
    pub body: Vec<TokenTree>,
    pub empty: Option<Vec<TokenTree>>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RelativePath {
    pub at: At,
    pub path: String,
}

#[derive(Clone, Debug, PartialEq)]
pub enum IncludeTemplateName {
    Text(Text),
    Variable(TagElement),
    Relative(RelativePath),
}

#[derive(Clone, Debug)]
pub struct Include {
    pub template_name: IncludeTemplateName,
    pub origin: Option<String>,
    pub engine: Arc<Engine>,
    pub only: bool,
    pub kwargs: Vec<(At, TagElement)>,
}

impl PartialEq for Include {
    fn eq(&self, other: &Self) -> bool {
        // We use `Arc::ptr_eq` here to avoid needing the `py` token for true
        // equality comparison between two `Py` smart pointers.
        //
        // We only use `eq` in tests, so this concession is acceptable here.
        self.only == other.only
            && self.origin == other.origin
            && self.template_name.eq(&other.template_name)
            && self.kwargs == other.kwargs
            && Arc::ptr_eq(&self.engine, &other.engine)
    }
}

#[derive(Clone, Debug)]
pub struct SimpleTag {
    pub func: Arc<Py<PyAny>>,
    pub at: At,
    pub takes_context: bool,
    pub args: Vec<TagElement>,
    pub kwargs: Vec<(String, TagElement)>,
    pub target_var: Option<String>,
}

impl PartialEq for SimpleTag {
    fn eq(&self, other: &Self) -> bool {
        // We use `Arc::ptr_eq` here to avoid needing the `py` token for true
        // equality comparison between two `Py` smart pointers.
        //
        // We only use `eq` in tests, so this concession is acceptable here.
        self.at == other.at
            && self.takes_context == other.takes_context
            && self.args == other.args
            && self.kwargs == other.kwargs
            && self.target_var == other.target_var
            && Arc::ptr_eq(&self.func, &other.func)
    }
}

#[derive(Clone, Debug)]
pub struct SimpleBlockTag {
    pub func: Arc<Py<PyAny>>,
    pub nodes: Vec<TokenTree>,
    pub at: At,
    pub takes_context: bool,
    pub args: Vec<TagElement>,
    pub kwargs: Vec<(String, TagElement)>,
    pub target_var: Option<String>,
}

impl PartialEq for SimpleBlockTag {
    fn eq(&self, other: &Self) -> bool {
        // We use `Arc::ptr_eq` here to avoid needing the `py` token for true
        // equality comparison between two `Py` smart pointers.
        //
        // We only use `eq` in tests, so this concession is acceptable here.
        self.at == other.at
            && self.takes_context == other.takes_context
            && self.args == other.args
            && self.kwargs == other.kwargs
            && self.target_var == other.target_var
            && self.nodes == other.nodes
            && Arc::ptr_eq(&self.func, &other.func)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Now {
    pub format: String,
    pub asvar: Option<At>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Tag {
    Autoescape {
        enabled: AutoescapeEnabled,
        nodes: Vec<TokenTree>,
    },
    If {
        condition: IfCondition,
        truthy: Vec<TokenTree>,
        falsey: Option<Vec<TokenTree>>,
    },
    For(For),
    Include(Include),
    Load,
    SimpleTag(SimpleTag),
    SimpleBlockTag(SimpleBlockTag),
    Url(Url),
    CsrfToken(CsrfToken),
    Lorem(Lorem),
    Comment(Comment),
    Now(Now),
    TemplateTag(TemplateTag),
}

#[derive(PartialEq, Eq)]
enum EndTagType {
    Autoescape,
    Elif,
    Else,
    EndIf,
    Empty,
    EndFor,
    Verbatim,
    Custom(String),
}

impl EndTagType {
    fn as_cow(&self) -> Cow<'static, str> {
        let end_tag = match self {
            Self::Autoescape => "endautoescape",
            Self::Elif => "elif",
            Self::Else => "else",
            Self::EndIf => "endif",
            Self::Empty => "empty",
            Self::EndFor => "endfor",
            Self::Verbatim => "endverbatim",
            Self::Custom(s) => return Cow::Owned(s.clone()),
        };
        Cow::Borrowed(end_tag)
    }
}

#[derive(PartialEq, Eq)]
struct EndTag {
    at: At,
    end: EndTagType,
    parts: Option<TagParts>,
}

impl EndTag {
    fn as_cow(&self) -> Cow<'static, str> {
        self.end.as_cow()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum TokenTree {
    Text(Text),
    TranslatedText(Text),
    Int(BigInt),
    Float(f64),
    Tag(Tag),
    Variable(Variable),
    ForVariable(ForVariable),
    Filter(Box<Filter>),
}

impl From<TagElement> for TokenTree {
    fn from(tag_element: TagElement) -> Self {
        match tag_element {
            TagElement::Text(text) => Self::Text(text),
            TagElement::TranslatedText(text) => Self::TranslatedText(text),
            TagElement::Variable(variable) => Self::Variable(variable),
            TagElement::ForVariable(variable) => Self::ForVariable(variable),
            TagElement::Filter(filter) => Self::Filter(filter),
            TagElement::Int(n) => Self::Int(n),
            TagElement::Float(f) => Self::Float(f),
        }
    }
}

impl From<Either<Variable, ForVariable>> for TagElement {
    fn from(variable: Either<Variable, ForVariable>) -> Self {
        match variable {
            Either::Left(v) => Self::Variable(v),
            Either::Right(v) => Self::ForVariable(v),
        }
    }
}

impl From<Either<Variable, ForVariable>> for ArgumentType {
    fn from(variable: Either<Variable, ForVariable>) -> Self {
        match variable {
            Either::Left(v) => Self::Variable(v),
            Either::Right(v) => Self::ForVariable(v),
        }
    }
}

#[allow(clippy::enum_variant_names)]
#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum ForParseError {
    #[error("Expected another variable when unpacking in for loop:")]
    MissingVariable {
        #[label("after this variable")]
        at: SourceSpan,
    },
    #[error("Expected a variable name before the 'in' keyword:")]
    MissingVariableBeforeIn {
        #[label("before this keyword")]
        at: SourceSpan,
    },
    #[error("Expected at least one variable name in for loop:")]
    MissingVariableNames {
        #[label("in this tag")]
        at: SourceSpan,
    },
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum ParseError {
    #[error("Empty variable tag")]
    EmptyVariable {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Expected an argument")]
    MissingArgument {
        #[label("here")]
        at: SourceSpan,
    },
    #[error(transparent)]
    #[diagnostic(transparent)]
    AutoescapeError(#[from] AutoescapeError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    BlockError(#[from] TagLexerError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    LexerError(#[from] LexerError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    ForLexerError(#[from] ForLexerError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    ForLexerInError(#[from] ForLexerInError),
    #[allow(clippy::enum_variant_names)]
    #[error(transparent)]
    #[diagnostic(transparent)]
    ForParseError(#[from] ForParseError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    IncludeLexerError(#[from] IncludeLexerError),
    #[error("{literal} is not iterable")]
    NotIterable {
        literal: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error(transparent)]
    #[diagnostic(transparent)]
    RelativePathError(#[from] RelativePathError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    TagElementKwargLexerError(#[from] TagElementKwargLexerError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    VariableError(#[from] VariableLexerError),
    #[error("The 'only' option was specified more than once.")]
    #[diagnostic(help("Remove the second 'only'"))]
    IncludeOnlyTwice {
        #[label("first here")]
        first_at: SourceSpan,
        #[label("second here")]
        second_at: SourceSpan,
    },
    #[error("Invalid filter: '{filter}'")]
    InvalidFilter {
        filter: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Not expecting '{token}' in this position")]
    InvalidIfPosition {
        token: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Invalid numeric literal")]
    InvalidNumber {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Missing boolean expression")]
    MissingBooleanExpression {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Unclosed '{start}' tag. Looking for one of: {expected}")]
    MissingEndTag {
        start: Cow<'static, str>,
        expected: Cow<'static, str>,
        #[label("started here")]
        at: SourceSpan,
    },
    #[error("'{tag}' is not a valid tag or filter in tag library '{library}'")]
    MissingFilterTag {
        tag: String,
        library: String,
        #[label("tag or filter")]
        tag_at: SourceSpan,
        #[label("library")]
        library_at: SourceSpan,
    },
    #[error("Expected a keyword argument")]
    MissingKeywordArgument {
        #[label("after this")]
        at: SourceSpan,
    },
    #[error("'{library}' is not a registered tag library.")]
    MissingTagLibrary {
        library: String,
        #[label("here")]
        at: SourceSpan,
        #[help]
        help: String,
    },
    #[error("Cannot mix arguments and keyword arguments")]
    MixedArgsKwargs {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'url' view name must be a string or variable, not a number")]
    NumericUrlName {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'{name}' must have a first argument of 'content'")]
    RequiresContent {
        name: String,
        #[label("loaded here")]
        at: SourceSpan,
    },
    #[error(
        "'{name}' is decorated with takes_context=True so it must have a first argument of 'context'"
    )]
    RequiresContext {
        name: String,
        #[label("loaded here")]
        at: SourceSpan,
    },
    #[error(
        "'{name}' is decorated with takes_context=True so it must have a first argument of 'context' and a second argument of 'content'"
    )]
    RequiresContextAndContent {
        name: String,
        #[label("loaded here")]
        at: SourceSpan,
    },
    #[error("'{tag_name}' did not receive value(s) for the argument(s): {missing}")]
    MissingArguments {
        tag_name: String,
        missing: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'{tag_name}' received multiple values for keyword argument '{kwarg_name}'")]
    DuplicateKeywordArgument {
        tag_name: String,
        kwarg_name: String,
        #[label("first")]
        first_at: SourceSpan,
        #[label("second")]
        second_at: SourceSpan,
    },
    #[error("Unexpected positional argument after keyword argument")]
    PositionalAfterKeyword {
        #[label("this positional argument")]
        at: SourceSpan,
        #[label("after this keyword argument")]
        after: SourceSpan,
    },
    #[error("Unexpected positional argument")]
    TooManyPositionalArguments {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Unexpected keyword argument")]
    UnexpectedKeywordArgument {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("{filter} filter does not take an argument")]
    UnexpectedArgument {
        filter: &'static str,
        #[label("unexpected argument")]
        at: SourceSpan,
    },
    #[error("Unexpected end of expression")]
    UnexpectedEndExpression {
        #[label("after this")]
        at: SourceSpan,
    },
    #[error("Unexpected tag {unexpected}")]
    UnexpectedEndTag {
        unexpected: Cow<'static, str>,
        #[label("unexpected tag")]
        at: SourceSpan,
    },
    #[error("Unused expression '{expression}' in if tag")]
    UnusedExpression {
        expression: String,
        #[label("here")]
        at: SourceSpan,
    },
    #[error("'url' takes at least one argument, a URL pattern name")]
    UrlTagNoArguments {
        #[label("here")]
        at: SourceSpan,
    },
    #[error("Unexpected tag {unexpected}, expected {expected}")]
    WrongEndTag {
        unexpected: Cow<'static, str>,
        expected: String,
        #[label("unexpected tag")]
        at: SourceSpan,
        #[label("start tag")]
        start_at: SourceSpan,
    },
    #[error("Incorrect format for '{tag}' tag")]
    InvalidTagFormat {
        tag: &'static str,
        #[label("here")]
        at: SourceSpan,
    },

    #[error("Invalid variable name")]
    InvalidVariableName {
        #[label("here")]
        at: SourceSpan,
    },

    #[error(transparent)]
    #[diagnostic(transparent)]
    LoremError(#[from] LoremError),

    #[error(transparent)]
    #[diagnostic(transparent)]
    NowError(#[from] NowError),

    #[error(transparent)]
    #[diagnostic(transparent)]
    TemplateTagError(#[from] TemplateTagError),

    #[error("Expected a variable name after 'as'")]
    #[diagnostic(help("Provide a name to store the date string, e.g. 'as my_var'"))]
    MissingVariableAfterAs {
        #[label("expected a variable name here")]
        at: SourceSpan,
    },

    #[error("Unexpected tokens after 'as {var_name}'")]
    #[diagnostic(help("Remove the extra tokens."))]
    UnexpectedTokensAfterAsVariable {
        var_name: Cow<'static, str>,
        #[label("unexpected tokens here")]
        at: SourceSpan,
    },
}

#[derive(Error, Debug)]
pub enum PyParseError {
    #[error(transparent)]
    PyErr(#[from] PyErr),
    #[error(transparent)]
    ParseError(#[from] ParseError),
}

impl PyParseError {
    pub fn try_into_parse_error(self) -> PyResult<ParseError> {
        match self {
            Self::ParseError(err) => Ok(err),
            Self::PyErr(err) => Err(err),
        }
    }

    #[cfg(test)]
    pub fn unwrap_parse_error(self) -> ParseError {
        match self {
            Self::ParseError(err) => err,
            Self::PyErr(err) => panic!("{err:?}"),
        }
    }
}

trait LoadLibrary {
    fn load_library<'l, 'py>(
        &self,
        py: Python<'py>,
        libraries: &'l HashMap<String, Py<PyAny>>,
        template: TemplateString<'_>,
    ) -> Result<&'l Bound<'py, PyAny>, ParseError>;
}
impl LoadLibrary for LoadToken {
    fn load_library<'l, 'py>(
        &self,
        py: Python<'py>,
        libraries: &'l HashMap<String, Py<PyAny>>,
        template: TemplateString<'_>,
    ) -> Result<&'l Bound<'py, PyAny>, ParseError> {
        let library_name = template.content(self.at);
        match libraries.get(library_name) {
            Some(library) => Ok(library.bind(py)),
            None => {
                let mut libraries: Vec<_> = libraries.keys().map(String::as_str).collect();
                libraries.sort_unstable();
                let help = format!("Must be one of:\n{}", libraries.join("\n"));
                Err(ParseError::MissingTagLibrary {
                    at: self.at.into(),
                    library: library_name.to_string(),
                    help,
                })
            }
        }
    }
}

#[derive(Debug, Clone)]
struct SimpleTagContext<'py> {
    func: Bound<'py, PyAny>,
    function_name: String,
    takes_context: bool,
    params: Vec<String>,
    defaults_count: usize,
    varargs: bool,
    kwonly: Vec<String>,
    kwonly_defaults: HashSet<String>,
    varkw: bool,
}

#[derive(Clone)]
enum TagContext<'py> {
    Simple(SimpleTagContext<'py>),
    SimpleBlock {
        end_tag_name: String,
        context: SimpleTagContext<'py>,
    },
    EndSimpleBlock,
}

pub struct Parser<'t, 'py> {
    py: Python<'py>,
    template: TemplateString<'t>,
    lexer: Lexer<'t>,
    engine: Arc<Engine>,
    origin: Option<&'t str>,
    external_tags: HashMap<String, TagContext<'py>>,
    external_filters: HashMap<String, Bound<'py, PyAny>>,
    forloop_depth: usize,
}

impl<'t, 'py> Parser<'t, 'py> {
    pub fn new(
        py: Python<'py>,
        template: TemplateString<'t>,
        engine: Arc<Engine>,
        origin: Option<&'t str>,
    ) -> Self {
        Self {
            py,
            template,
            lexer: Lexer::new(template),
            engine,
            origin,
            external_tags: HashMap::new(),
            external_filters: HashMap::new(),
            forloop_depth: 0,
        }
    }

    #[cfg(test)]
    fn new_with_filters(
        py: Python<'py>,
        template: TemplateString<'t>,
        external_filters: HashMap<String, Bound<'py, PyAny>>,
    ) -> Self {
        Self {
            py,
            template,
            lexer: Lexer::new(template),
            engine: Engine::empty().into(),
            origin: None,
            external_tags: HashMap::new(),
            external_filters,
            forloop_depth: 0,
        }
    }

    pub fn parse(&mut self) -> Result<Vec<TokenTree>, PyParseError> {
        let mut nodes = Vec::new();
        while let Some(token) = self.lexer.next() {
            let node = match token.token_type {
                TokenType::Text => TokenTree::Text(Text::new(token.at)),
                TokenType::Comment => continue,
                TokenType::Variable => self
                    .parse_variable(token.content(self.template), token.at, token.trimmed_at().0)?
                    .into(),
                TokenType::Tag => match self.parse_tag(token.content(self.template), token.at)? {
                    Either::Left(token_tree) => token_tree,
                    Either::Right(end_tag) => {
                        return Err(ParseError::UnexpectedEndTag {
                            at: end_tag.at.into(),
                            unexpected: end_tag.as_cow(),
                        }
                        .into());
                    }
                },
            };
            nodes.push(node);
        }
        Ok(nodes)
    }

    fn parse_until(
        &mut self,
        until: Vec<EndTagType>,
        start: Cow<'static, str>,
        start_at: At,
    ) -> Result<(Vec<TokenTree>, EndTag), PyParseError> {
        let mut nodes = Vec::new();
        while let Some(token) = self.lexer.next() {
            let node = match token.token_type {
                TokenType::Text => TokenTree::Text(Text::new(token.at)),
                TokenType::Comment => continue,
                TokenType::Variable => self
                    .parse_variable(token.content(self.template), token.at, token.trimmed_at().0)?
                    .into(),
                TokenType::Tag => match self.parse_tag(token.content(self.template), token.at)? {
                    Either::Left(token_tree) => token_tree,
                    Either::Right(end_tag) => {
                        if until.contains(&end_tag.end) {
                            return Ok((nodes, end_tag));
                        }
                        return Err(ParseError::WrongEndTag {
                            expected: until
                                .iter()
                                .map(EndTagType::as_cow)
                                .collect::<Vec<_>>()
                                .join(", "),
                            unexpected: end_tag.as_cow(),
                            at: end_tag.at.into(),
                            start_at: start_at.into(),
                        }
                        .into());
                    }
                },
            };
            nodes.push(node);
        }
        Err(ParseError::MissingEndTag {
            start,
            expected: until
                .iter()
                .map(EndTagType::as_cow)
                .collect::<Vec<_>>()
                .join(", ")
                .into(),
            at: start_at.into(),
        }
        .into())
    }

    fn parse_for_variable(&self, at: At) -> Either<Variable, ForVariable> {
        let mut parts = self.template.content(at).split('.');
        if self.forloop_depth == 0
            || parts
                .next()
                .expect("a variable can always be split into at least one part")
                .trim()
                != "forloop"
        {
            return Either::Left(Variable::new(at));
        }
        let Some(part) = parts.next_back() else {
            return Either::Right(ForVariable {
                variant: ForVariableName::Object,
                parent_count: 0,
                at,
            });
        };
        let variant = match part.trim() {
            "counter" => ForVariableName::Counter,
            "counter0" => ForVariableName::Counter0,
            "revcounter" => ForVariableName::RevCounter,
            "revcounter0" => ForVariableName::RevCounter0,
            "first" => ForVariableName::First,
            "last" => ForVariableName::Last,
            "parentloop" => ForVariableName::Object,
            _ => return Either::Left(Variable::new(at)),
        };
        let parts: Vec<_> = parts.collect();
        for part in &parts {
            if part.trim() != "parentloop" {
                return Either::Left(Variable::new(at));
            }
        }
        let mut parent_count = parts.len();
        if variant == ForVariableName::Object {
            parent_count += 1;
        }
        if parent_count > self.forloop_depth {
            return Either::Left(Variable::new(at));
        }
        Either::Right(ForVariable {
            variant,
            parent_count,
            at,
        })
    }

    fn parse_variable(
        &self,
        variable: &str,
        at: At,
        start: usize,
    ) -> Result<TagElement, ParseError> {
        let Some((variable_token, at, filter_lexer)) = lex_variable_or_filter(variable, start)?
        else {
            return Err(ParseError::EmptyVariable { at: at.into() });
        };
        let mut var = match variable_token {
            VariableToken::Variable => self.parse_for_variable(at).into(),
            VariableToken::Int(n) => TagElement::Int(n),
            VariableToken::Float(f) => TagElement::Float(f),
        };
        for filter_token in filter_lexer {
            let filter_token = filter_token?;
            let argument = match filter_token.argument {
                None => None,
                Some(ref a) => Some(a.parse(self)?),
            };
            let filter_at = (at.0, filter_token.at.0 - at.0 + filter_token.at.1);
            let filter = Filter::new(self, filter_token.at, filter_at, var, argument)?;
            var = TagElement::Filter(Box::new(filter));
        }
        Ok(var)
    }

    fn parse_lorem(&mut self, _at: At, parts: TagParts) -> Result<Lorem, PyParseError> {
        let mut lexer = LoremLexer::new(self.template, parts);

        let first = match lexer.next() {
            None => {
                return Ok(Lorem {
                    count: TagElement::Int(1.into()),
                    method: LoremMethod::Blocks,
                    common: true,
                });
            }
            Some(first) => first.map_err(ParseError::from)?,
        };

        let second = match lexer.next() {
            None => match first.token_type {
                LoremTokenType::Method(method) => {
                    return Ok(Lorem {
                        count: TagElement::Int(1.into()),
                        method,
                        common: true,
                    });
                }
                LoremTokenType::Count(token) => {
                    let count = token.parse(self)?;
                    return Ok(Lorem {
                        count,
                        method: LoremMethod::Blocks,
                        common: true,
                    });
                }
                LoremTokenType::Random => {
                    return Ok(Lorem {
                        count: TagElement::Int(1.into()),
                        method: LoremMethod::Blocks,
                        common: false,
                    });
                }
            },
            Some(second) => second.map_err(ParseError::from)?,
        };

        let count = self.parse_variable(self.template.content(first.at), first.at, first.at.0)?;
        let third = match lexer.next() {
            None => match second.token_type {
                LoremTokenType::Method(method) => {
                    return Ok(Lorem {
                        count,
                        method,
                        common: true,
                    });
                }
                LoremTokenType::Random => {
                    return Ok(Lorem {
                        count,
                        method: LoremMethod::Blocks,
                        common: false,
                    });
                }
                _ => unreachable!("Count in second position should already have errored"),
            },
            Some(third) => third.map_err(ParseError::from)?,
        };

        if let Some(fourth) = lexer.next() {
            fourth.map_err(ParseError::from)?;
            unreachable!(
                "A fourth argument should be a duplicate count, method or random, which is already an error"
            )
        }

        match (second.token_type, third.token_type) {
            (LoremTokenType::Method(method), LoremTokenType::Random) => Ok(Lorem {
                count,
                method,
                common: false,
            }),
            _ => unreachable!("Should already have errored"),
        }
    }

    fn parse_comment(&mut self, at: At, _parts: TagParts) -> Result<Comment, PyParseError> {
        for token in self.lexer.by_ref() {
            if let TokenType::Tag = token.token_type {
                let content = token.content(self.template).trim();
                if content.split_whitespace().next() == Some("endcomment") {
                    return Ok(Comment);
                }
            }
        }

        Err(ParseError::MissingEndTag {
            start: "comment".into(),
            expected: "endcomment".into(),
            at: at.into(),
        }
        .into())
    }

    fn parse_now(&mut self, parts: TagParts) -> Result<Now, PyParseError> {
        let mut lexer = NowLexer::new(self.template, parts);

        let format_at = lexer.lex_format().map_err(ParseError::from)?;
        let asvar = lexer.lex_variable().map_err(ParseError::from)?;
        lexer.extra_token().map_err(ParseError::from)?;
        let raw = self.template.content(format_at);
        // Django always trims the first and last character without further
        // validation, so so do we. This will become unnecessary if Django
        // starts supporting variables in the now tag.
        // https://github.com/django/new-features/issues/115
        let format = if raw.len() >= 2 {
            &raw[1..raw.len() - 1]
        } else {
            ""
        };

        Ok(Now {
            format: format.to_string(),
            asvar,
        })
    }

    fn parse_tag(
        &mut self,
        tag: &'t str,
        at: At,
    ) -> Result<Either<TokenTree, EndTag>, PyParseError> {
        let tag = lex_tag(tag, at.0 + START_TAG_LEN).map_err(ParseError::from)?;

        Ok(match tag.content(self.template) {
            "url" => Either::Left(self.parse_url(at, tag.parts)?),
            "csrf_token" => Either::Left(TokenTree::Tag(Tag::CsrfToken(CsrfToken))),
            "load" => Either::Left(self.parse_load(at, tag.parts)?),
            "autoescape" => Either::Left(self.parse_autoescape(at, tag.parts)?),
            "endautoescape" => Either::Right(EndTag {
                end: EndTagType::Autoescape,
                at,
                parts: None,
            }),
            "endverbatim" => Either::Right(EndTag {
                end: EndTagType::Verbatim,
                at,
                parts: None,
            }),
            "if" => Either::Left(self.parse_if(at, tag.parts, "if")?),
            "elif" => Either::Right(EndTag {
                end: EndTagType::Elif,
                at,
                parts: Some(tag.parts),
            }),
            "else" => Either::Right(EndTag {
                end: EndTagType::Else,
                at,
                parts: None,
            }),
            "endif" => Either::Right(EndTag {
                end: EndTagType::EndIf,
                at,
                parts: None,
            }),
            "for" => Either::Left(self.parse_for(at, tag.parts)?),
            "empty" => Either::Right(EndTag {
                end: EndTagType::Empty,
                at,
                parts: None,
            }),
            "endfor" => Either::Right(EndTag {
                end: EndTagType::EndFor,
                at,
                parts: None,
            }),
            "include" => Either::Left(self.parse_include(at, tag.parts)?),
            "lorem" => Either::Left(TokenTree::Tag(Tag::Lorem(self.parse_lorem(at, tag.parts)?))),
            "comment" => Either::Left(TokenTree::Tag(Tag::Comment(
                self.parse_comment(at, tag.parts)?,
            ))),
            "now" => Either::Left(TokenTree::Tag(Tag::Now(self.parse_now(tag.parts)?))),
            "templatetag" => Either::Left(TokenTree::Tag(Tag::TemplateTag(
                lex_templatetag(self.template, tag.parts).map_err(ParseError::from)?,
            ))),
            tag_name => match self.external_tags.get(tag_name) {
                Some(TagContext::Simple(context)) => {
                    Either::Left(self.parse_simple_tag(context, at, tag.parts)?)
                }
                Some(TagContext::SimpleBlock {
                    context,
                    end_tag_name,
                }) => Either::Left(self.parse_simple_block_tag(
                    context.clone(),
                    tag_name.to_string(),
                    end_tag_name.clone(),
                    at,
                    tag.parts,
                )?),
                Some(TagContext::EndSimpleBlock) => Either::Right(EndTag {
                    end: EndTagType::Custom(tag_name.to_string()),
                    at,
                    parts: None,
                }),
                None => todo!("{tag_name}"),
            },
        })
    }

    #[allow(clippy::type_complexity)]
    fn parse_custom_tag_parts(
        &self,
        parts: TagParts,
        context: &SimpleTagContext,
    ) -> Result<(Vec<TagElement>, Vec<(String, TagElement)>, Option<String>), ParseError> {
        let mut args = Vec::new();
        let mut kwargs = Vec::new();

        let parts_at = parts.at;
        let mut prev_at = parts.at;
        let mut seen_kwargs: HashMap<&str, At> = HashMap::new();
        let params_count = context.params.len();
        let mut tokens =
            TagElementKwargLexer::new(self.template, parts).collect::<Result<Vec<_>, _>>()?;
        let asvar = extract_as_variable(&mut tokens, &self.template)?;
        for (index, token) in tokens.iter().enumerate() {
            match token.kwarg {
                None => {
                    if !seen_kwargs.is_empty() {
                        return Err(ParseError::PositionalAfterKeyword {
                            at: token.at.into(),
                            after: prev_at.into(),
                        });
                    }
                    if !context.varargs && index == params_count {
                        return Err(ParseError::TooManyPositionalArguments {
                            at: token.at.into(),
                        });
                    }
                    let element = token.parse(self)?;
                    args.push(element);
                    prev_at = token.at;
                }
                Some(name_at) => {
                    let kwarg_at = (name_at.0, name_at.1 + 1 + token.at.1);
                    let name = self.template.content(name_at);
                    if !context.varkw
                        && !context.params.iter().any(|a| a == name)
                        && !context.kwonly.iter().any(|kw| kw == name)
                    {
                        return Err(ParseError::UnexpectedKeywordArgument {
                            at: kwarg_at.into(),
                        });
                    } else if let Some(&first_at) = seen_kwargs.get(name) {
                        return Err(ParseError::DuplicateKeywordArgument {
                            tag_name: context.function_name.clone(),
                            kwarg_name: name.to_string(),
                            first_at: first_at.into(),
                            second_at: kwarg_at.into(),
                        });
                    }
                    let element = token.parse(self)?;
                    seen_kwargs.insert(name, kwarg_at);
                    kwargs.push((name.to_string(), element));
                    prev_at = kwarg_at;
                }
            }
        }

        let args_count = args.len();
        let mut missing_params = Vec::new();
        if params_count > args_count + context.defaults_count {
            for param in &context.params[args_count..params_count - context.defaults_count] {
                if !seen_kwargs.contains_key(param.as_str()) {
                    missing_params.push(param.clone());
                }
            }
        }
        for kwarg in &context.kwonly {
            if !seen_kwargs.contains_key(kwarg.as_str())
                && !context.kwonly_defaults.contains(kwarg.as_str())
            {
                missing_params.push(kwarg.clone());
            }
        }
        if !missing_params.is_empty() {
            let missing = missing_params
                .iter()
                .map(|p| format!("'{p}'"))
                .collect::<Vec<_>>()
                .join(", ");
            return Err(ParseError::MissingArguments {
                tag_name: context.function_name.clone(),
                at: parts_at.into(),
                missing,
            });
        }
        Ok((args, kwargs, asvar))
    }

    fn parse_simple_tag(
        &self,
        context: &SimpleTagContext,
        at: At,
        parts: TagParts,
    ) -> Result<TokenTree, PyParseError> {
        let (args, kwargs, target_var) = self.parse_custom_tag_parts(parts, context)?;
        let tag = SimpleTag {
            func: context.func.clone().unbind().into(),
            at,
            takes_context: context.takes_context,
            args,
            kwargs,
            target_var,
        };
        Ok(TokenTree::Tag(Tag::SimpleTag(tag)))
    }

    fn parse_simple_block_tag(
        &mut self,
        context: SimpleTagContext,
        tag_name: String,
        end_tag_name: String,
        at: At,
        parts: TagParts,
    ) -> Result<TokenTree, PyParseError> {
        let (args, kwargs, target_var) = self.parse_custom_tag_parts(parts, &context)?;
        let (nodes, _) = self.parse_until(
            vec![EndTagType::Custom(end_tag_name)],
            Cow::Owned(tag_name),
            at,
        )?;
        let tag = SimpleBlockTag {
            func: context.func.clone().unbind().into(),
            nodes,
            at,
            takes_context: context.takes_context,
            args,
            kwargs,
            target_var,
        };
        Ok(TokenTree::Tag(Tag::SimpleBlockTag(tag)))
    }

    fn parse_load(&mut self, at: At, parts: TagParts) -> Result<TokenTree, PyParseError> {
        let tokens: Vec<_> = LoadLexer::new(self.template, parts).collect();
        let mut rev = tokens.iter().rev();
        if let (Some(last), Some(prev)) = (rev.next(), rev.next())
            && self.template.content(prev.at) == "from"
        {
            let library = last.load_library(self.py, &self.engine.libraries, self.template)?;
            let filters = self.get_filters(library)?;
            let tags = self.get_tags(library)?;
            for token in rev {
                let content = self.template.content(token.at);
                if let Some(filter) = filters.get(content) {
                    self.external_filters
                        .insert(content.to_string(), filter.clone());
                } else if let Some(tag) = tags.get(content) {
                    self.load_tag(token.at, content, tag)?;
                } else {
                    return Err(ParseError::MissingFilterTag {
                        library: self.template.content(last.at).to_string(),
                        library_at: last.at.into(),
                        tag: content.to_string(),
                        tag_at: token.at.into(),
                    }
                    .into());
                }
            }
            return Ok(TokenTree::Tag(Tag::Load));
        }
        for token in tokens {
            let library = token.load_library(self.py, &self.engine.libraries, self.template)?;
            let filters = self.get_filters(library)?;
            let tags = self.get_tags(library)?;
            self.external_filters.extend(filters);
            for (name, tag) in &tags {
                self.load_tag(at, name, tag)?;
            }
        }
        Ok(TokenTree::Tag(Tag::Load))
    }

    #[allow(clippy::too_many_lines)]
    fn load_tag(
        &mut self,
        at: At,
        name: &str,
        tag: &Bound<'py, PyAny>,
    ) -> Result<(), PyParseError> {
        let closure = tag.getattr("__closure__")?;
        let tag = if closure.is_none() {
            todo!("Fully custom tag")
        } else {
            let tag_code = tag.getattr("__code__")?;
            let closure_names: Vec<String> = tag_code.getattr("co_freevars")?.extract()?;
            let closure_values = closure
                .try_iter()?
                .map(|v| v?.getattr("cell_contents"))
                .collect::<Result<Vec<_>, _>>()?;

            if closure_names.contains(&"filename".to_string()) {
                todo!("Inclusion tag")
            } else if closure_names.contains(&"end_name".to_string()) {
                let defaults_count = get_defaults_count(&closure_values[0])?;
                let end_tag_name: String = closure_values[1].extract()?;
                let func = closure_values[2].clone();
                let function_name = closure_values[3].extract()?;
                let kwonly = closure_values[4].extract()?;
                let kwonly_defaults = get_kwonly_defaults(&closure_values[5])?;
                let params: Vec<String> = closure_values[6].extract()?;
                let takes_context = closure_values[7].is_truthy()?;
                let varargs = !closure_values[8].is_none();
                let varkw = !closure_values[9].is_none();

                let params = match takes_context {
                    false => {
                        if let Some(param) = params.first()
                            && param == "content"
                        {
                            params.iter().skip(1).cloned().collect()
                        } else {
                            return Err(ParseError::RequiresContent {
                                name: function_name,
                                at: at.into(),
                            }
                            .into());
                        }
                    }
                    true => {
                        if let Some([context, content]) = params.first_chunk::<2>()
                            && context == "context"
                            && content == "content"
                        {
                            params.iter().skip(2).cloned().collect()
                        } else {
                            return Err(ParseError::RequiresContextAndContent {
                                name: function_name,
                                at: at.into(),
                            }
                            .into());
                        }
                    }
                };
                // TODO: `end_tag_name already present?
                self.external_tags
                    .insert(end_tag_name.clone(), TagContext::EndSimpleBlock);
                TagContext::SimpleBlock {
                    end_tag_name,
                    context: SimpleTagContext {
                        func,
                        function_name,
                        takes_context,
                        params,
                        defaults_count,
                        varargs,
                        kwonly,
                        kwonly_defaults,
                        varkw,
                    },
                }
            } else {
                let defaults_count = get_defaults_count(&closure_values[0])?;
                let func = closure_values[1].clone();
                let function_name = closure_values[2].extract()?;
                let kwonly = closure_values[3].extract()?;
                let kwonly_defaults = get_kwonly_defaults(&closure_values[4])?;
                let params: Vec<String> = closure_values[5].extract()?;
                let takes_context = closure_values[6].is_truthy()?;
                let varargs = !closure_values[7].is_none();
                let varkw = !closure_values[8].is_none();

                let params = match takes_context {
                    false => params,
                    true => {
                        if let Some(param) = params.first()
                            && param == "context"
                        {
                            params.iter().skip(1).cloned().collect()
                        } else {
                            return Err(ParseError::RequiresContext {
                                name: function_name,
                                at: at.into(),
                            }
                            .into());
                        }
                    }
                };
                TagContext::Simple(SimpleTagContext {
                    func,
                    function_name,
                    takes_context,
                    params,
                    defaults_count,
                    varargs,
                    kwonly,
                    kwonly_defaults,
                    varkw,
                })
            }
        };
        self.external_tags.insert(name.to_string(), tag);
        Ok(())
    }

    fn get_tags(
        &self,
        library: &Bound<'py, PyAny>,
    ) -> PyResult<HashMap<String, Bound<'py, PyAny>>> {
        library.getattr(intern!(self.py, "tags"))?.extract()
    }

    fn get_filters(
        &self,
        library: &Bound<'py, PyAny>,
    ) -> PyResult<HashMap<String, Bound<'py, PyAny>>> {
        library.getattr(intern!(self.py, "filters"))?.extract()
    }

    fn parse_url(&self, at: At, parts: TagParts) -> Result<TokenTree, ParseError> {
        let mut lexer = TagElementKwargLexer::new(self.template, parts);
        let Some(view_token) = lexer.next() else {
            return Err(ParseError::UrlTagNoArguments { at: at.into() });
        };
        let view_name = view_token?.parse(self)?;

        let mut tokens = lexer.collect::<Result<Vec<_>, _>>()?;
        let asvar = extract_as_variable(&mut tokens, &self.template)?;

        let mut args = vec![];
        let mut kwargs = vec![];
        for token in tokens {
            let element = token.parse(self)?;
            match token.kwarg {
                None => args.push(element),
                Some(at) => {
                    let kwarg = self.template.content(at).to_string();
                    kwargs.push((kwarg, element));
                }
            }
        }
        if !args.is_empty() && !kwargs.is_empty() {
            return Err(ParseError::MixedArgsKwargs { at: at.into() });
        }
        let url = Url {
            view_name,
            args,
            kwargs,
            asvar,
        };
        Ok(TokenTree::Tag(Tag::Url(url)))
    }

    fn parse_include(&self, at: At, parts: TagParts) -> Result<TokenTree, ParseError> {
        let mut lexer = IncludeLexer::new(self.template, parts);
        let Some(template_token) = lexer.lex_template()? else {
            return Err(ParseError::MissingArgument { at: at.into() });
        };
        let template_name = match parse_include_template_token(template_token, self)? {
            IncludeTemplateName::Text(Text { at }) => {
                let template_path = self.template.content(at);
                match construct_relative_path(template_path, self.origin, at)? {
                    Some(path) => IncludeTemplateName::Relative(RelativePath {
                        path: path.into_owned(),
                        at,
                    }),
                    None => IncludeTemplateName::Text(Text { at }),
                }
            }
            template_name => template_name,
        };

        let mut only = None;
        let mut with = None;
        let mut kwargs = Vec::new();
        match lexer.lex_with_or_only()? {
            IncludeWithToken::None => {}
            IncludeWithToken::Only(at) => {
                match lexer.lex_with_or_only()? {
                    IncludeWithToken::None => {}
                    IncludeWithToken::Only(second_at) => {
                        return Err(ParseError::IncludeOnlyTwice {
                            first_at: at.into(),
                            second_at: second_at.into(),
                        });
                    }
                    IncludeWithToken::With(at) => with = Some(at),
                }
                only = Some(at);
            }
            IncludeWithToken::With(at) => with = Some(at),
        }
        if let Some(with_at) = with {
            for token in lexer {
                match token? {
                    IncludeToken::Only(at) => match only {
                        None => only = Some(at),
                        Some(first_at) => {
                            return Err(ParseError::IncludeOnlyTwice {
                                first_at: first_at.into(),
                                second_at: at.into(),
                            });
                        }
                    },
                    IncludeToken::Kwarg { kwarg_at, token } => {
                        let element = token.parse(self)?;
                        kwargs.push((kwarg_at, element));
                    }
                }
            }
            if kwargs.is_empty() {
                return Err(ParseError::MissingKeywordArgument { at: with_at.into() });
            }
        }
        let include = Include {
            template_name,
            origin: self.origin.map(ToString::to_string),
            engine: self.engine.clone(),
            kwargs,
            only: only.is_some(),
        };
        Ok(TokenTree::Tag(Tag::Include(include)))
    }

    fn parse_autoescape(&mut self, at: At, parts: TagParts) -> Result<TokenTree, PyParseError> {
        let token = lex_autoescape_argument(self.template, parts).map_err(ParseError::from)?;
        let (nodes, _) = self.parse_until(vec![EndTagType::Autoescape], "autoescape".into(), at)?;
        Ok(TokenTree::Tag(Tag::Autoescape {
            enabled: token.enabled,
            nodes,
        }))
    }

    fn parse_if(
        &mut self,
        at: At,
        parts: TagParts,
        start: &'static str,
    ) -> Result<TokenTree, PyParseError> {
        let condition = parse_if_condition(self, parts, at)?;
        let (nodes, end_tag) = self.parse_until(
            vec![EndTagType::Elif, EndTagType::Else, EndTagType::EndIf],
            start.into(),
            at,
        )?;
        let falsey = match end_tag {
            EndTag {
                at,
                end: EndTagType::Elif,
                parts: Some(parts),
            } => Some(vec![self.parse_if(at, parts, "elif")?]),
            EndTag {
                at,
                end: EndTagType::Else,
                parts: None,
            } => {
                let (nodes, _) = self.parse_until(vec![EndTagType::EndIf], "else".into(), at)?;
                Some(nodes)
            }
            EndTag {
                at: _end_at,
                end: EndTagType::EndIf,
                parts: None,
            } => None,
            _ => unreachable!(),
        };
        Ok(TokenTree::Tag(Tag::If {
            condition,
            truthy: nodes,
            falsey,
        }))
    }

    fn parse_for(&mut self, at: At, parts: TagParts) -> Result<TokenTree, PyParseError> {
        self.forloop_depth += 1;
        let (iterable, variables, reversed) = parse_for_loop(self, parts, at)?;
        let (nodes, end_tag) = self.parse_until(
            vec![EndTagType::Empty, EndTagType::EndFor],
            "for".into(),
            at,
        )?;
        self.forloop_depth -= 1;
        let empty = match end_tag {
            EndTag {
                at,
                end: EndTagType::Empty,
                parts: _parts,
            } => {
                let (nodes, _) = self.parse_until(vec![EndTagType::EndFor], "empty".into(), at)?;
                Some(nodes)
            }
            EndTag {
                at: _end_at,
                end: EndTagType::EndFor,
                parts: _parts,
            } => None,
            _ => unreachable!(),
        };
        Ok(TokenTree::Tag(Tag::For(For {
            iterable,
            variables,
            reversed,
            body: nodes,
            empty,
        })))
    }
}

fn get_defaults_count(defaults: &Bound<'_, PyAny>) -> PyResult<usize> {
    match defaults.is_none() {
        true => Ok(0),
        false => defaults.len(),
    }
}

fn get_kwonly_defaults(kwonly_defaults: &Bound<'_, PyAny>) -> PyResult<HashSet<String>> {
    match kwonly_defaults.is_none() {
        true => Ok(HashSet::new()),
        false => kwonly_defaults
            .try_iter()?
            .map(|item| item?.extract())
            .collect::<PyResult<_>>(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyDict, PyDictMethods};

    use crate::{
        filters::{DefaultFilter, ExternalFilter, LowerFilter},
        template::django_rusty_templates::{Engine, Template},
    };
    use dtl_lexer::common::LexerError;

    fn get_external_filter(node: &TokenTree) -> Arc<Py<PyAny>> {
        match node {
            TokenTree::Filter(filter) => match &filter.filter {
                FilterType::External(filter) => filter.filter.clone(),
                _ => panic!(),
            },
            _ => panic!(),
        }
    }

    fn get_external_filter_tag_element(node: &TokenTree) -> Arc<Py<PyAny>> {
        match node {
            TokenTree::Filter(filter) => match &filter.left {
                TagElement::Filter(filter) => match &filter.filter {
                    FilterType::External(filter) => filter.filter.clone(),
                    _ => panic!(),
                },
                _ => panic!(),
            },
            _ => panic!(),
        }
    }

    #[test]
    fn test_empty_template() {
        Python::initialize();

        Python::attach(|py| {
            let template = "";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();
            assert_eq!(nodes, vec![]);
        });
    }

    #[test]
    fn test_text() {
        Python::initialize();

        Python::attach(|py| {
            let template = "Some text";
            let template_string = TemplateString(template);
            let mut parser = Parser::new(py, template_string, Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();
            let text = Text::new((0, template.len()));
            assert_eq!(nodes, vec![TokenTree::Text(text)]);
            assert_eq!(template_string.content(text.at), template);
        });
    }

    #[test]
    fn test_comment() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{# A comment #}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();
            assert_eq!(nodes, vec![]);
        });
    }

    #[test]
    fn test_empty_variable() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ }}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(error, ParseError::EmptyVariable { at: (0, 5).into() });
        });
    }

    #[test]
    fn test_variable() {
        Python::initialize();

        Python::attach(|py| {
            let template = TemplateString("{{ foo }}");
            let mut parser = Parser::new(py, template, Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();
            let variable = Variable { at: (3, 3) };
            assert_eq!(nodes, vec![TokenTree::Variable(variable)]);
            assert_eq!(
                variable.parts(template).collect::<Vec<_>>(),
                vec![("foo", (3, 3))]
            );
        });
    }

    #[test]
    fn test_variable_attribute() {
        Python::initialize();

        Python::attach(|py| {
            let template = TemplateString("{{ foo.bar.baz }}");
            let mut parser = Parser::new(py, template, Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();
            let variable = Variable { at: (3, 11) };
            assert_eq!(nodes, vec![TokenTree::Variable(variable)]);
            assert_eq!(
                variable.parts(template).collect::<Vec<_>>(),
                vec![("foo", (3, 3)), ("bar", (7, 3)), ("baz", (11, 3))]
            );
        });
    }

    #[test]
    fn test_filter() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = TemplateString("{{ foo|bar }}");
            let mut parser = Parser::new_with_filters(py, template, filters);
            let nodes = parser.parse().unwrap();

            assert_eq!(nodes.len(), 1);

            let foo = Variable { at: (3, 3) };
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: TagElement::Variable(foo),
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: None,
                }),
            }));
            assert_eq!(nodes, vec![bar]);
            assert_eq!(
                foo.parts(template).collect::<Vec<_>>(),
                vec![("foo", (3, 3))]
            );
        });
    }

    #[test]
    fn test_unknown_filter() {
        Python::initialize();

        Python::attach(|py| {
            let template = TemplateString("{{ foo|bar }}");
            let mut parser = Parser::new(py, template, Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::InvalidFilter {
                    filter: "bar".to_string(),
                    at: (7, 3).into()
                }
            );
        });
    }

    #[test]
    fn test_filter_multiple() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ foo|bar|baz }}";
            let filters = HashMap::from([
                ("bar".to_string(), py.None().bind(py).clone()),
                ("baz".to_string(), py.None().bind(py).clone()),
            ]);
            let mut parser = Parser::new_with_filters(py, template.into(), filters);
            let nodes = parser.parse().unwrap();
            assert_eq!(nodes.len(), 1);

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let external = get_external_filter_tag_element(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TagElement::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: None,
                }),
            }));
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let baz = TokenTree::Filter(Box::new(Filter {
                at: (11, 3),
                all_at: (3, 11),
                left: bar,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: None,
                }),
            }));
            assert_eq!(nodes, vec![baz]);
        });
    }

    #[test]
    fn test_filter_argument() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = TemplateString("{{ foo|bar:baz }}");
            let mut parser = Parser::new_with_filters(py, template, filters);
            let nodes = parser.parse().unwrap();
            assert_eq!(nodes.len(), 1);

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let baz = Variable { at: (11, 3) };
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(Argument {
                        at: (11, 3),
                        argument_type: ArgumentType::Variable(baz),
                    }),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
            assert_eq!(
                baz.parts(template).collect::<Vec<_>>(),
                vec![("baz", (11, 3))]
            );
        });
    }

    #[test]
    fn test_filter_argument_text() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = TemplateString("{{ foo|bar:'baz' }}");
            let mut parser = Parser::new_with_filters(py, template, filters);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let baz = Text::new((12, 3));
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(Argument {
                        at: (11, 5),
                        argument_type: ArgumentType::Text(baz),
                    }),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
            assert_eq!(template.content(baz.at), "baz");
        });
    }

    #[test]
    fn test_filter_argument_translated_text() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = TemplateString("{{ foo|bar:_('baz') }}");
            let mut parser = Parser::new_with_filters(py, template, filters);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let baz = TranslatedText::new((14, 3));
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(Argument {
                        at: (11, 8),
                        argument_type: ArgumentType::TranslatedText(baz),
                    }),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
            assert_eq!(template.content(baz.at), "baz");
        });
    }

    #[test]
    fn test_filter_argument_float() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = "{{ foo|bar:5.2e3 }}";
            let mut parser = Parser::new_with_filters(py, template.into(), filters);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let num = Argument {
                at: (11, 5),
                argument_type: ArgumentType::Float(5.2e3),
            };
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(num),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
        });
    }

    #[test]
    fn test_filter_argument_int() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = "{{ foo|bar:99 }}";
            let mut parser = Parser::new_with_filters(py, template.into(), filters);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let num = Argument {
                at: (11, 2),
                argument_type: ArgumentType::Int(99.into()),
            };
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(num),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
        });
    }

    #[test]
    fn test_filter_argument_bigint() {
        Python::initialize();

        Python::attach(|py| {
            let filters = HashMap::from([("bar".to_string(), py.None().bind(py).clone())]);
            let template = "{{ foo|bar:99999999999999999 }}";
            let mut parser = Parser::new_with_filters(py, template.into(), filters);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let num = Argument {
                at: (11, 17),
                argument_type: ArgumentType::Int("99999999999999999".parse::<BigInt>().unwrap()),
            };
            let external = get_external_filter(&nodes[0]);
            assert!(external.is_none(py));
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 3),
                all_at: (3, 7),
                left: foo,
                filter: FilterType::External(ExternalFilter {
                    filter: external,
                    argument: Some(num),
                }),
            }));
            assert_eq!(nodes, vec![bar]);
        });
    }

    #[test]
    fn test_filter_argument_invalid_number() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ foo|bar:9.9.9 }}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(error, ParseError::InvalidNumber { at: (11, 5).into() });
        });
    }

    #[test]
    fn test_filter_parse_addslashes() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ foo|addslashes }}".to_string();
            let context = PyDict::new(py);
            context.set_item("bar", "").unwrap();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "");

            let context = PyDict::new(py);
            context.set_item("foo", "").unwrap();
            let template_string = "{{ foo|addslashes:invalid }}".to_string();
            let error = Template::new_from_string(py, template_string, engine).unwrap_err();

            let error_string = format!("{error}");
            assert!(error_string.contains("addslashes filter does not take an argument"));
        });
    }

    #[test]
    fn test_filter_default() {
        Python::initialize();

        Python::attach(|py| {
            let template = TemplateString("{{ foo|default:baz }}");
            let mut parser = Parser::new(py, template, Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let foo = TagElement::Variable(Variable { at: (3, 3) });
            let baz = Variable { at: (15, 3) };
            let bar = TokenTree::Filter(Box::new(Filter {
                at: (7, 7),
                all_at: (3, 11),
                left: foo,
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (15, 3),
                        argument_type: ArgumentType::Variable(baz),
                    },
                    (7, 7),
                )),
            }));
            assert_eq!(nodes, vec![bar]);
            assert_eq!(
                baz.parts(template).collect::<Vec<_>>(),
                vec![("baz", (15, 3))]
            );
        });
    }

    #[test]
    fn test_filter_default_missing_argument() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ foo|default|baz }}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(error, ParseError::MissingArgument { at: (7, 7).into() });
        });
    }

    #[test]
    fn test_filter_lower_unexpected_argument() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ foo|lower:baz }}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::UnexpectedArgument {
                    filter: "lower",
                    at: (13, 3).into()
                }
            );
        });
    }

    #[test]
    fn test_variable_lexer_error() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{{ _foo }}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::VariableError(
                    LexerError::InvalidVariableName { at: (3, 4).into() }.into()
                )
            );
        });
    }

    #[test]
    fn test_parse_empty_tag() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{%  %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::BlockError(TagLexerError::EmptyTag { at: (0, 6).into() })
            );
        });
    }

    #[test]
    fn test_block_error() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url'foo' %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::BlockError(TagLexerError::InvalidTagName { at: (3, 8).into() })
            );
        });
    }

    #[test]
    fn test_parse_url_tag() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url 'some-url-name' %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Text(Text { at: (8, 13) }),
                args: vec![],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_view_name_translated() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url _('some-url-name') %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::TranslatedText(Text { at: (10, 13) }),
                args: vec![],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_view_name_variable() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_view_name_filter() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name|default:'home' %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let some_view_name = TagElement::Variable(Variable { at: (7, 14) });
            let home = Text { at: (31, 4) };
            let default = Box::new(Filter {
                at: (22, 7),
                all_at: (7, 22),
                left: some_view_name,
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (30, 6),
                        argument_type: ArgumentType::Text(home),
                    },
                    (22, 7),
                )),
            });
            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Filter(default),
                args: vec![],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_no_arguments() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(error, ParseError::UrlTagNoArguments { at: (0, 9).into() });
        });
    }

    #[test]
    fn test_parse_url_view_name_integer() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url 64 %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Int(64.into()),
                args: vec![],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_arguments() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name 'foo' bar|default:'home' 64 5.7 _(\"spam\") %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![
                    TagElement::Text(Text { at: (23, 3) }),
                    TagElement::Filter(Box::new(Filter {
                        at: (32, 7),
                        all_at: (28, 11),
                        left: TagElement::Variable(Variable { at: (28, 3) }),
                        filter: FilterType::Default(DefaultFilter::new(
                            Argument {
                                at: (40, 6),
                                argument_type: ArgumentType::Text(Text { at: (41, 4) }),
                            },
                            (32, 7),
                        )),
                    })),
                    TagElement::Int(64.into()),
                    TagElement::Float(5.7),
                    TagElement::TranslatedText(Text { at: (57, 4) }),
                ],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_kwargs() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name foo='foo' extra=-64 %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![],
                kwargs: vec![
                    ("foo".to_string(), TagElement::Text(Text { at: (27, 3) })),
                    ("extra".to_string(), TagElement::Int((-64).into())),
                ],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_arguments_as_variable() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name 'foo' as some_url %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![TagElement::Text(Text { at: (23, 3) })],
                kwargs: vec![],
                asvar: Some("some_url".to_string()),
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_kwargs_as_variable() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name foo='foo' as some_url %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![],
                kwargs: vec![("foo".to_string(), TagElement::Text(Text { at: (27, 3) }))],
                asvar: Some("some_url".to_string()),
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_arguments_last_variables() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name 'foo' arg arg2 %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let nodes = parser.parse().unwrap();

            let url = TokenTree::Tag(Tag::Url(Url {
                view_name: TagElement::Variable(Variable { at: (7, 14) }),
                args: vec![
                    TagElement::Text(Text { at: (23, 3) }),
                    TagElement::Variable(Variable { at: (28, 3) }),
                    TagElement::Variable(Variable { at: (32, 4) }),
                ],
                kwargs: vec![],
                asvar: None,
            }));

            assert_eq!(nodes, vec![url]);
        });
    }

    #[test]
    fn test_parse_url_tag_mixed_args_kwargs() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url some_view_name 'foo' arg name=arg2 %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(
                error,
                ParseError::MixedArgsKwargs {
                    at: (0, template.len()).into()
                }
            );
        });
    }

    #[test]
    fn test_parse_url_tag_invalid_number() {
        Python::initialize();

        Python::attach(|py| {
            let template = "{% url foo 9.9.9 %}";
            let mut parser = Parser::new(py, template.into(), Engine::empty().into(), None);
            let error = parser.parse().unwrap_err().unwrap_parse_error();
            assert_eq!(error, ParseError::InvalidNumber { at: (11, 5).into() });
        });
    }

    #[test]
    fn test_filter_type_partial_eq() {
        Python::initialize();

        Python::attach(|py| {
            assert_eq!(
                FilterType::Lower(LowerFilter),
                FilterType::Lower(LowerFilter)
            );
            assert_ne!(
                FilterType::External(ExternalFilter::new(py.None(), None)),
                FilterType::External(ExternalFilter::new(py.None(), None))
            );
            assert_ne!(
                FilterType::Lower(LowerFilter),
                FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (0, 3),
                        argument_type: ArgumentType::Float(1.0)
                    },
                    (0, 7)
                ))
            );
        });
    }

    #[test]
    fn test_simple_tag_partial_eq() {
        Python::initialize();

        Python::attach(|py| {
            let func: Arc<Py<PyAny>> = PyDict::new(py).into_any().unbind().into();
            let at = (0, 1);
            let takes_context = true;
            assert_eq!(
                SimpleTag {
                    func: func.clone(),
                    at,
                    takes_context,
                    args: Vec::new(),
                    kwargs: Vec::new(),
                    target_var: Some("foo".to_string()),
                },
                SimpleTag {
                    func,
                    at,
                    takes_context,
                    args: Vec::new(),
                    kwargs: Vec::new(),
                    target_var: Some("foo".to_string()),
                },
            );
        });
    }

    #[test]
    fn test_simple_block_tag_partial_eq() {
        Python::initialize();

        Python::attach(|py| {
            let func: Arc<Py<PyAny>> = PyDict::new(py).into_any().unbind().into();
            let at = (0, 1);
            let takes_context = true;
            assert_eq!(
                SimpleBlockTag {
                    func: func.clone(),
                    at,
                    takes_context,
                    args: Vec::new(),
                    kwargs: Vec::new(),
                    nodes: Vec::new(),
                    target_var: Some("foo".to_string()),
                },
                SimpleBlockTag {
                    func,
                    at,
                    takes_context,
                    args: Vec::new(),
                    kwargs: Vec::new(),
                    nodes: Vec::new(),
                    target_var: Some("foo".to_string()),
                },
            );
        });
    }

    #[test]
    fn test_include_tag_partial_eq() {
        Python::initialize();

        Python::attach(|_| {
            let engine: Arc<Engine> = Engine::empty().into();
            let template_name = IncludeTemplateName::Variable(TagElement::Float(1.1));
            assert_eq!(
                Include {
                    template_name: template_name.clone(),
                    origin: None,
                    only: false,
                    kwargs: Vec::new(),
                    engine: engine.clone(),
                },
                Include {
                    template_name,
                    origin: None,
                    only: false,
                    kwargs: Vec::new(),
                    engine,
                },
            );
        });
    }
}
