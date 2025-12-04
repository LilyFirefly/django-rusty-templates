use std::borrow::Cow;
use std::sync::LazyLock;

use html_escape::encode_quoted_attribute_to_string;
use num_traits::ToPrimitive;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;
use pyo3::types::{PyDate, PyDateTime, PyTime};

use crate::error::{AnnotatePyErr, PyRenderError, RenderError};
use crate::filters::{
    AddFilter, AddSlashesFilter, CapfirstFilter, CenterFilter, CutFilter, DateFilter,
    DefaultFilter, DefaultIfNoneFilter, EscapeFilter, EscapejsFilter, ExternalFilter, FilterType,
    LengthFilter, LowerFilter, SafeFilter, SlugifyFilter, TitleFilter, UpperFilter,
    WordcountFilter, WordwrapFilter, YesnoFilter,
};
use crate::parse::Filter;
use crate::render::common::gettext;
use crate::render::types::{AsBorrowedContent, Content, ContentString, Context, IntoOwnedContent};
use crate::render::{Resolve, ResolveFailures, ResolveResult};
use dtl_lexer::types::TemplateString;
use regex::Regex;
use unicode_normalization::UnicodeNormalization;

// Used for replacing all non-word and non-spaces with an empty string
static NON_WORD_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[^\w\s-]").expect("Static string will never panic"));

// regex for whitespaces and hyphen, used for replacing with hyphen only
static WHITESPACE_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[-\s]+").expect("Static string will never panic"));

static SAFEDATA: PyOnceLock<Py<PyType>> = PyOnceLock::new();
static GET_FORMAT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static DATE_FORMAT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

impl Resolve for Filter {
    fn resolve<'t, 'py>(
        &self,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
        failures: ResolveFailures,
    ) -> ResolveResult<'t, 'py> {
        let left = self.left.resolve(py, template, context, failures)?;
        match &self.filter {
            FilterType::Add(filter) => filter.resolve(left, py, template, context),
            FilterType::AddSlashes(filter) => filter.resolve(left, py, template, context),
            FilterType::Capfirst(filter) => filter.resolve(left, py, template, context),
            FilterType::Center(filter) => filter.resolve(left, py, template, context),
            FilterType::Cut(filter) => filter.resolve(left, py, template, context),
            FilterType::Default(filter) => filter.resolve(left, py, template, context),
            FilterType::DefaultIfNone(filter) => filter.resolve(left, py, template, context),
            FilterType::Date(filter) => filter.resolve(left, py, template, context),
            FilterType::Escape(filter) => filter.resolve(left, py, template, context),
            FilterType::Escapejs(filter) => filter.resolve(left, py, template, context),
            FilterType::External(filter) => filter.resolve(left, py, template, context),
            FilterType::Lower(filter) => filter.resolve(left, py, template, context),
            FilterType::Length(filter) => filter.resolve(left, py, template, context),
            FilterType::Safe(filter) => filter.resolve(left, py, template, context),
            FilterType::Slugify(filter) => filter.resolve(left, py, template, context),
            FilterType::Title(filter) => filter.resolve(left, py, template, context),
            FilterType::Upper(filter) => filter.resolve(left, py, template, context),
            FilterType::Wordcount(filter) => filter.resolve(left, py, template, context),
            FilterType::Wordwrap(filter) => filter.resolve(left, py, template, context),
            FilterType::Yesno(filter) => filter.resolve(left, py, template, context),
        }
    }
}

pub trait ResolveFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py>;
}

impl ResolveFilter for AddSlashesFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => {
                let content_string = content.resolve_string(context)?;
                content_string.map_content(|raw| {
                    Cow::Owned(
                        raw.replace('\\', r"\\")
                            .replace('"', "\\\"")
                            .replace('\'', r"\'"),
                    )
                })
            }
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for AddFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(variable) = variable else {
            return Ok(None);
        };
        let right = self
            .argument
            .resolve(py, template, context, ResolveFailures::Raise)?
            .expect("missing argument in context should already have raised");
        Ok(match (variable.to_bigint(), right.to_bigint()) {
            (Some(variable), Some(right)) => Some(Content::Int(variable + right)),
            _ => {
                let variable = variable.to_py(py);
                let right = right.to_py(py);
                variable.add(right).ok().map(Content::Py)
            }
        })
    }
}

impl ResolveFilter for CapfirstFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => {
                let content_string = content.render(context)?.into_owned();
                let mut chars = content_string.chars();
                let first_char = match chars.next() {
                    Some(c) => c.to_uppercase(),
                    None => return Ok(Some("".as_content())),
                };
                let string: String = first_char.chain(chars).collect();
                string.into_content()
            }
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for CenterFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(content) = variable else {
            return Ok(Some("".as_content()));
        };
        let content = content.render(context)?;
        let arg = self
            .argument
            .resolve(py, template, context, ResolveFailures::Raise)?
            .expect("missing argument in context should already have raised");

        let size = arg.resolve_usize(self.argument.at)?;

        if size <= content.len() {
            return Ok(Some(content.into_content()));
        }
        let round_up = size % 2 == 0 && content.len() % 2 != 0;
        let right = if round_up {
            // If the size is even and the content length is odd, we need to adjust the centering
            (size - content.len()).div_ceil(2)
        } else {
            (size - content.len()) / 2
        };
        let left = size - content.len() - right;

        let mut centered = String::with_capacity(size);

        centered.push_str(&" ".repeat(left));
        centered.push_str(&content);
        centered.push_str(&" ".repeat(right));

        Ok(Some(centered.into_content()))
    }
}

fn cut(source: Cow<'_, str>, value: &str) -> String {
    source.replace(value, "")
}

impl ResolveFilter for CutFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(variable) = variable else {
            return Ok(Some("".as_content()));
        };

        let arg = self
            .argument
            .resolve(py, template, context, ResolveFailures::Raise)?
            .expect("missing argument in context should already have raised")
            .resolve_string_strict(context, self.argument.at.into())?
            .into_raw();

        let content_string = variable.resolve_string(context)?;
        let result = match content_string {
            ContentString::String(s) => ContentString::String(cut(s, &arg).into()),
            ContentString::HtmlSafe(s) => {
                let cut = cut(s, &arg);
                match arg.as_ref() {
                    ";" => ContentString::HtmlUnsafe(cut.into()),
                    _ => ContentString::HtmlSafe(cut.into()),
                }
            }
            ContentString::HtmlUnsafe(s) => ContentString::HtmlUnsafe(cut(s, &arg).into()),
        };

        Ok(Some(Content::String(result)))
    }
}

impl ResolveFilter for DefaultFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        match variable {
            Some(left)
                if left
                    .to_bool()
                    .map_err(|err| err.annotate(py, self.at, "here", template))? =>
            {
                Ok(Some(left))
            }
            None | Some(_) => self
                .argument
                .resolve(py, template, context, ResolveFailures::Raise),
        }
    }
}

impl ResolveFilter for DefaultIfNoneFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        match variable {
            Some(Content::Py(ref value)) if value.is_none() => {
                self.argument
                    .resolve(py, template, context, ResolveFailures::Raise)
            }
            Some(left) => Ok(Some(left)),
            None => Ok(Some("".as_content())),
        }
    }
}

impl ResolveFilter for DateFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(value) = variable else {
            return Ok(Some("".as_content()));
        };

        let fmt = match &self.argument {
            Some(arg) => arg
                .resolve(py, template, context, ResolveFailures::Raise)?
                .expect("missing argument in context should already have raised")
                .to_py(py),
            None => {
                let get_format = GET_FORMAT.import(py, "django.utils.formats", "get_format")?;
                get_format.call1(("DATE_FORMAT",))?
            }
        };

        let value = value.to_py(py);

        let is_valid = value.is_instance_of::<PyDate>()
            || value.is_instance_of::<PyTime>()
            || value.is_instance_of::<PyDateTime>();

        if !is_valid {
            return Ok(Some("".as_content()));
        }

        let date_format_fn = DATE_FORMAT.import(py, "django.utils.dateformat", "format")?;

        let formatted = match date_format_fn.call1((value, fmt)) {
            Ok(res) => res,
            Err(e) => {
                if e.is_instance_of::<pyo3::exceptions::PyAttributeError>(py) {
                    return Ok(Some("".as_content()));
                }
                return Err(PyRenderError::PyErr(
                    e.annotate(py, self.at, "here", template),
                ));
            }
        };

        Ok(Some(Content::Py(formatted)))
    }
}

impl ResolveFilter for EscapeFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        _context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        Ok(Some(Content::String(ContentString::HtmlSafe(
            match variable {
                Some(content) => match content {
                    Content::String(ContentString::HtmlSafe(content)) => content,
                    Content::String(content) => {
                        let mut encoded = String::new();
                        encode_quoted_attribute_to_string(content.as_raw(), &mut encoded);
                        Cow::Owned(encoded)
                    }
                    Content::Int(n) => Cow::Owned(n.to_string()),
                    Content::Float(n) => Cow::Owned(n.to_string()),
                    Content::Py(object) => {
                        let content = object.str()?.extract::<String>()?;
                        let mut encoded = String::new();
                        encode_quoted_attribute_to_string(&content, &mut encoded);
                        Cow::Owned(encoded)
                    }
                    Content::Bool(true) => Cow::Borrowed("True"),
                    Content::Bool(false) => Cow::Borrowed("False"),
                },
                None => Cow::Borrowed(""),
            },
        ))))
    }
}

/// Hex encode characters for use in JavaScript strings.
fn escapejs(value: &str) -> String {
    let mut result = String::with_capacity(value.len());
    for ch in value.chars() {
        match ch {
            '\\' => result.push_str(r"\u005C"),
            '\'' => result.push_str(r"\u0027"),
            '"' => result.push_str(r"\u0022"),
            '>' => result.push_str(r"\u003E"),
            '<' => result.push_str(r"\u003C"),
            '&' => result.push_str(r"\u0026"),
            '=' => result.push_str(r"\u003D"),
            '-' => result.push_str(r"\u002D"),
            ';' => result.push_str(r"\u003B"),
            '`' => result.push_str(r"\u0060"),
            // Line separator
            '\u{2028}' => result.push_str(r"\u2028"),
            // Paragraph Separator
            '\u{2029}' => result.push_str(r"\u2029"),
            // c as u32 is safe because all chars are valid u32
            // See https://doc.rust-lang.org/std/primitive.char.html#method.from_u32
            c if matches!(c, '\0'..='\x1f') => {
                result.push_str(&format!(r"\u{:04X}", c as u32));
            }
            c => result.push(c),
        }
    }
    result
}

impl ResolveFilter for EscapejsFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => content
                .resolve_string(context)?
                .map_content(|content| Cow::Owned(escapejs(&content))),
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for ExternalFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let arg = match &self.argument {
            Some(arg) => arg.resolve(py, template, context, ResolveFailures::Raise)?,
            None => None,
        };
        let filter = self.filter.bind(py);
        let value = match arg {
            Some(arg) => filter.call1((variable, arg))?,
            None => filter.call1((variable,))?,
        };
        Ok(Some(Content::Py(value)))
    }
}

impl ResolveFilter for LowerFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => content
                .resolve_string(context)?
                .map_content(|content| Cow::Owned(content.to_lowercase())),
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for LengthFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        _context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let len = match variable {
            None => 0,
            Some(Content::String(s)) => s.as_raw().chars().count(),
            Some(Content::Py(obj)) => obj.len().unwrap_or(0),
            Some(Content::Int(_) | Content::Float(_) | Content::Bool(_)) => 0,
        };

        Ok(Some(Content::Int(num_bigint::BigInt::from(len))))
    }
}

impl ResolveFilter for SafeFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        _context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        Ok(Some(Content::String(ContentString::HtmlSafe(
            match variable {
                Some(content) => match content {
                    Content::String(content) => content.into_raw(),
                    Content::Int(n) => Cow::Owned(n.to_string()),
                    Content::Float(n) => Cow::Owned(n.to_string()),
                    Content::Py(object) => {
                        let content = object.str()?.extract::<String>()?;
                        Cow::Owned(content)
                    }
                    Content::Bool(true) => Cow::Borrowed("True"),
                    Content::Bool(false) => Cow::Borrowed("False"),
                },
                None => Cow::Borrowed(""),
            },
        ))))
    }
}

pub fn slugify(content: Cow<str>) -> Cow<str> {
    let content = content
        .nfkd()
        // first decomposing characters, then only keeping
        // the ascii ones, filtering out diacritics for example.
        .filter(char::is_ascii)
        .collect::<String>()
        .to_lowercase();
    let content = NON_WORD_RE.replace_all(&content, "");
    let content = content.trim();
    let content = WHITESPACE_RE.replace_all(content, "-");
    Cow::Owned(content.to_string())
}

impl ResolveFilter for SlugifyFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        _template: TemplateString<'t>,
        _context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => match content {
                Content::Py(content) => {
                    let slug = slugify(Cow::Owned(content.str()?.extract::<String>()?));
                    #[allow(non_snake_case)]
                    let SafeData = SAFEDATA.import(py, "django.utils.safestring", "SafeData")?;
                    match content.is_instance(SafeData)? {
                        true => Content::String(ContentString::HtmlSafe(slug)),
                        false => Content::String(ContentString::HtmlUnsafe(slug)),
                    }
                }
                // Int and Float requires no slugify, we only need to turn it into a string.
                Content::Int(content) => content.to_string().into_content(),
                Content::Float(content) => content.to_string().into_content(),
                Content::String(content) => content.map_content(slugify),
                Content::Bool(true) => "true".as_content(),
                Content::Bool(false) => "false".as_content(),
            },
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for TitleFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(content) = variable else {
            return Ok(Some("".as_content()));
        };
        let content_string = content.resolve_string(context)?;

        Ok(Some(content_string.map_content(|content| {
            let mut result = String::with_capacity(content.len());
            let mut prev = None;
            let mut prev_letter_was_lowercased = false;

            for ch in content.chars() {
                if ch.is_alphabetic() {
                    // Django's special cases to trigger lowercase:
                    // 1. After apostrophe that follows a lowercased letter
                    // 2. After a digit
                    let should_lowercase = match prev {
                        Some('\'') if prev_letter_was_lowercased => true,
                        Some(c) if c.is_ascii_digit() | c.is_alphabetic() => true,
                        _ => false,
                    };

                    if should_lowercase {
                        result.extend(ch.to_lowercase());
                    } else {
                        result.extend(ch.to_uppercase());
                    }
                    prev_letter_was_lowercased = should_lowercase;
                } else {
                    result.push(ch);
                }
                prev = Some(ch);
            }
            Cow::Owned(result)
        })))
    }
}

impl ResolveFilter for UpperFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => {
                let content = content.resolve_string(context)?;
                content.map_content(|content| Cow::Owned(content.to_uppercase()))
            }
            None => "".as_content(),
        };
        Ok(Some(content))
    }
}

impl ResolveFilter for WordcountFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            Some(content) => {
                let content_string = content.resolve_string(context)?;
                let word_count = content_string.as_raw().split_whitespace().count();
                Content::Int(word_count.into())
            }
            None => Content::Int(0.into()),
        };
        Ok(Some(content))
    }
}

/// A word-wrap function that preserves existing line breaks.
/// Expects that existing line breaks are posix newlines.
///
/// Preserve all white space except added line breaks consume the space on
/// which they break the line.
///
/// Don't wrap long words, thus the output text may have lines longer than ``width``.
fn wordwrap(text: &str, width: usize) -> String {
    let mut result = String::with_capacity(text.len());

    for (i, line) in text.split('\n').enumerate() {
        if i > 0 {
            result.push('\n');
        }

        if line.is_empty() {
            continue;
        }

        let leading_whitespace = line.chars().take_while(|c| c.is_whitespace()).count();
        let (indent, trimmed_line) = line.split_at(leading_whitespace);

        let mut words = trimmed_line.split_whitespace();

        let Some(first_word) = words.next() else {
            // Line contains only whitespace - preserve it
            result.push_str(line);
            continue;
        };

        result.push_str(indent);
        result.push_str(first_word);

        let mut current_len = leading_whitespace + first_word.len();
        for word in words {
            let word_len = word.len();

            if current_len + word_len < width {
                result.push(' ');
                current_len += 1 + word_len;
            } else {
                result.push('\n');
                current_len = word_len;
            }
            result.push_str(word);
        }
    }

    result
}

impl ResolveFilter for WordwrapFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let Some(content) = variable else {
            return Ok(Some("".as_content()));
        };

        let text = content.resolve_string(context)?;

        let arg = self
            .argument
            .resolve(py, template, context, ResolveFailures::Raise)?
            .expect("missing argument in context should already have raised");

        // Check for negative values before converting to usize
        if let Some(bigint) = arg.to_bigint()
            && let Some(n) = bigint.to_isize()
            && n <= 0
        {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "invalid width {n} (must be > 0)"
            ))
            .annotate(py, self.argument.at, "width", template)
            .into());
        }

        let width = match arg.resolve_usize(self.argument.at) {
            Ok(w) => w,
            Err(PyRenderError::RenderError(RenderError::OverflowError { .. })) => usize::MAX,
            Err(e) => return Err(e),
        };

        let wrapped = wordwrap(text.as_raw(), width);
        Ok(Some(text.map_content(|_| Cow::Owned(wrapped))))
    }
}

impl ResolveFilter for YesnoFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: Option<Content<'t, 'py>>,
        py: Python<'py>,
        template: TemplateString<'t>,
        context: &mut Context,
    ) -> ResolveResult<'t, 'py> {
        let arg_string = match &self.argument {
            Some(arg) => {
                let arg_content = arg
                    .resolve(py, template, context, ResolveFailures::Raise)?
                    .expect("missing argument in context should already have raised");
                arg_content
                    .resolve_string_strict(context, arg.at.into())?
                    .into_raw()
            }
            None => Cow::Owned(gettext(py, "yes,no,maybe")?),
        };

        let bits: Vec<&str> = arg_string.split(',').collect();
        let (yes, no, maybe) = match bits.as_slice() {
            // If less than 2 values, return the original value
            [] | [_] => return Ok(variable),
            [yes, no] => (yes, no, no),
            [yes, no, maybe, ..] => (yes, no, maybe),
        };

        let result = match variable {
            Some(Content::Py(ref obj)) if obj.is_none() => maybe,
            Some(content) => match content.to_bool() {
                Ok(true) => yes,
                Ok(false) => no,
                Err(error) => {
                    let error = error.annotate(py, self.at, "when calling __bool__ here", template);
                    return Err(error.into());
                }
            },
            None => no,
        };

        Ok(Some(result.to_string().into_content()))
    }
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use super::*;
    use crate::filters::{AddSlashesFilter, DefaultFilter, LowerFilter, UpperFilter};
    use crate::parse::TagElement;
    use crate::render::Render;
    use crate::template::django_rusty_templates::{Engine, Template};
    use crate::types::{Argument, ArgumentType, Text};

    use pyo3::types::{PyDict, PyString};
    static MARK_SAFE: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

    fn mark_safe(py: Python<'_>, string: String) -> PyResult<Py<PyAny>> {
        let mark_safe = match MARK_SAFE.get(py) {
            Some(mark_safe) => mark_safe,
            None => {
                let py_mark_safe = py.import("django.utils.safestring")?;
                let py_mark_safe = py_mark_safe.getattr("mark_safe")?;
                MARK_SAFE.set(py, py_mark_safe.into()).unwrap();
                MARK_SAFE.get(py).unwrap()
            }
        };
        let safe_string = mark_safe.call1(py, (string,))?;
        Ok(safe_string)
    }

    use dtl_lexer::types::Variable;
    use std::collections::HashMap;

    #[test]
    fn test_render_filter() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|default:'Bryony' }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 7),
                all_at: (3, 12),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (16, 8),
                        argument_type: ArgumentType::Text(Text::new((17, 6))),
                    },
                    (8, 7),
                )),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "Lily");
        });
    }

    #[test]
    fn test_render_filter_slugify_happy_path() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "hello world").unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "hello-world");
        });
    }

    #[test]
    fn test_render_filter_slugify_spaces_omitted() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", " hello world").unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "hello-world");
        });
    }

    #[test]
    fn test_render_filter_slugify_special_characters_omitted() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "a&€%").unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "a");
        });
    }

    #[test]
    fn test_render_filter_slugify_multiple_spaces_inside_becomes_single() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "a & b").unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "a-b");
        });
    }

    #[test]
    fn test_render_filter_slugify_integer() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|default:1|slugify }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "1");
        });
    }

    #[test]
    fn test_render_filter_slugify_float() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|default:1.3|slugify }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "1.3");
        });
    }

    #[test]
    fn test_render_filter_slugify_rust_string() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|default:'hello world'|slugify }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "hello-world");
        });
    }

    #[test]
    fn test_render_filter_slugify_safe_string() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|default:'hello world'|safe|slugify }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "hello-world");
        });
    }

    #[test]
    fn test_render_filter_slugify_safe_string_from_rust_treated_as_py() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify }}".to_string();
            let context = PyDict::new(py);
            let safe_string = mark_safe(py, "a &amp; b".to_string()).unwrap();
            context.set_item("var", safe_string).unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "a-amp-b");
        });
    }

    #[test]
    fn test_render_filter_slugify_non_existing_variable() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ not_there|slugify }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "");
        });
    }

    #[test]
    fn test_render_filter_slugify_invalid() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|slugify:invalid }}".to_string();
            let error = Template::new_from_string(py, template_string, engine).unwrap_err();

            let error_string = format!("{error}");
            assert!(error_string.contains("slugify filter does not take an argument"));
        });
    }

    #[test]
    fn test_render_filter_addslashes_single() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "'hello'").into_any();
            let context = HashMap::from([("quotes".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ quotes|addslashes }}");
            let variable = Variable::new((3, 6));
            let filter = Filter {
                at: (10, 10),
                all_at: (3, 17),
                left: TagElement::Variable(variable),
                filter: FilterType::AddSlashes(AddSlashesFilter),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, r"\'hello\'");
        });
    }

    #[test]
    fn test_render_filter_capfirst() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|capfirst }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "hello world").unwrap();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "Hello world");

            let context = PyDict::new(py);
            context.set_item("var", "").unwrap();
            let template_string = "{{ var|capfirst }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "");

            let context = PyDict::new(py);
            context.set_item("bar", "").unwrap();
            let template_string = "{{ var|capfirst }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "");

            let template_string = "{{ var|capfirst:invalid }}".to_string();
            let error = Template::new_from_string(py, template_string, engine).unwrap_err();

            let error_string = format!("{error}");
            assert!(error_string.contains("capfirst filter does not take an argument"));
        });
    }

    #[test]
    fn test_render_filter_center() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|center:'11' }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "hello").unwrap();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "   hello   ");

            let context = PyDict::new(py);
            context.set_item("var", "django").unwrap();
            let template_string = "{{ var|center:'15' }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "     django    ");

            let context = PyDict::new(py);
            context.set_item("var", "django").unwrap();
            let template_string = "{{ var|center:1 }}".to_string();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "django");
        });
    }

    #[test]
    fn test_render_filter_center_no_argument_return_err() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|center }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "hello").unwrap();
            let error = Template::new_from_string(py, template_string, engine).unwrap_err();

            let error_string = format!("{error}");

            assert!(error_string.contains("Expected an argument"));
        });
    }

    #[test]
    fn test_render_filter_center_no_variable() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|center:'11' }}".to_string();
            let context = PyDict::new(py);
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "");
        });
    }

    #[test]
    fn test_render_filter_center_on_0() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|center:0 }}".to_string();
            let context = PyDict::new(py);
            context.set_item("var", "hello").unwrap();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template.py_render(py, Some(context), None).unwrap();

            assert_eq!(result, "hello");
        });
    }

    #[test]
    fn test_render_filter_default() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|default:'Bryony' }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 7),
                all_at: (3, 12),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (16, 8),
                        argument_type: ArgumentType::Text(Text::new((17, 6))),
                    },
                    (8, 7),
                )),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "Bryony");
        });
    }

    #[test]
    fn test_render_filter_default_integer() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ count|default:12}}");
            let variable = Variable::new((3, 5));
            let filter = Filter {
                at: (9, 7),
                all_at: (3, 12),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (17, 2),
                        argument_type: ArgumentType::Int(12.into()),
                    },
                    (9, 7),
                )),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "12");
        });
    }

    #[test]
    fn test_render_filter_default_float() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ count|default:3.5}}");
            let variable = Variable::new((3, 5));
            let filter = Filter {
                at: (9, 7),
                all_at: (3, 12),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (17, 3),
                        argument_type: ArgumentType::Float(3.5),
                    },
                    (9, 7),
                )),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "3.5");
        });
    }

    #[test]
    fn test_render_filter_default_variable() {
        Python::initialize();

        Python::attach(|py| {
            let me = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("me".to_string(), me.unbind())]);
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|default:me}}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 7),
                all_at: (3, 11),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (16, 2),
                        argument_type: ArgumentType::Variable(Variable::new((16, 2))),
                    },
                    (8, 7),
                )),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "Lily");
        });
    }

    #[test]
    fn test_render_filter_lower() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|lower }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Lower(LowerFilter),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "lily");
        });
    }

    #[test]
    fn test_render_filter_lower_missing_left() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|lower }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Lower(LowerFilter),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "");
        });
    }

    #[test]
    fn test_render_chained_filters() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|default:'Bryony'|lower }}");
            let variable = Variable::new((3, 4));
            let default = Filter {
                at: (8, 7),
                all_at: (3, 12),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (16, 8),
                        argument_type: ArgumentType::Text(Text::new((17, 6))),
                    },
                    (8, 7),
                )),
            };
            let lower = Filter {
                at: (25, 5),
                all_at: (3, 27),
                left: TagElement::Filter(Box::new(default)),
                filter: FilterType::Lower(LowerFilter),
            };

            let rendered = lower.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "bryony");
        });
    }

    #[test]
    fn test_render_filter_upper() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Foo").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|upper }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Upper(UpperFilter),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "FOO");
        });
    }

    #[test]
    fn test_render_filter_upper_missing_left() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false);
            let template = TemplateString("{{ name|upper }}");
            let variable = Variable::new((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Upper(UpperFilter),
            };

            let rendered = filter.render(py, template, &mut context).unwrap();
            assert_eq!(rendered, "");
        });
    }
}
