use std::borrow::Cow;

use html_escape::encode_quoted_attribute_to_string;
use num_traits::{ToPrimitive, Zero};
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;
use pyo3::types::{PyDate, PyDateTime, PyTime};

use crate::error::{AnnotatePyErr, PyRenderError, RenderError};
use crate::filters::{
    AddFilter, AddSlashesFilter, CapfirstFilter, CenterFilter, CutFilter, DateFilter,
    DefaultFilter, DefaultIfNoneFilter, DivisibleByFilter, EscapeFilter, EscapejsFilter,
    ExternalFilter, FilterType, ForceEscapeFilter, LastFilter, LengthFilter, LowerFilter,
    SafeFilter, SlugifyFilter, TitleFilter, UpperFilter, WordcountFilter, WordwrapFilter,
    YesnoFilter,
};
use crate::parse::Filter;
use crate::python_compat;
use crate::render::common::gettext;
use crate::render::types::{
    AsBorrowedContent, Content, ContentString, Context, IntoOwnedContent, PyContent,
};
use crate::render::{FileName, StringIfInvalid};
use crate::render::{Resolve, ResolveContent, ResolveFailures, ResolveResult};
use dtl_lexer::types::TemplateString;
use unicode_normalization::UnicodeNormalization;

static SAFEDATA: PyOnceLock<Py<PyType>> = PyOnceLock::new();
static GET_FORMAT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static DATE_FORMAT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

impl Resolve for Filter {
    #[allow(clippy::too_many_lines)]
    fn resolve<'t, 'py>(
        &self,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        failures: ResolveFailures,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let left = self.left.resolve(
            py,
            template,
            template_name,
            context,
            failures,
            string_if_invalid,
        )?;
        match &self.filter {
            FilterType::Add(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::AddSlashes(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Capfirst(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Center(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Cut(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Default(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::DefaultIfNone(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::DivisibleBy(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Date(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Escape(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Escapejs(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::External(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::ForceEscape(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Last(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Lower(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Length(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Safe(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Slugify(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Title(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Upper(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Wordcount(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Wordwrap(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
            FilterType::Yesno(filter) => filter.resolve(
                left,
                py,
                template,
                template_name,
                context,
                string_if_invalid,
            ),
        }
    }
}

pub trait ResolveFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py>;
}

impl ResolveFilter for AddSlashesFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => {
                let content_string = content.resolve_string(py, template, context)?;
                content_string.map_content(|raw| {
                    Cow::Owned(
                        raw.replace('\\', r"\\")
                            .replace('"', "\\\"")
                            .replace('\'', r"\'"),
                    )
                })
            }
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for AddFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let variable = match variable {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(missing) => return Ok(ResolveContent::Missing(missing)),
        };
        let right = match self.argument.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(_) => {
                unreachable!("missing argument in context should already have raised")
            }
        };
        Ok(ResolveContent::Content(
            match (variable.to_bigint(), right.to_bigint()) {
                (Some(variable), Some(right)) => Content::Int(variable + right),
                _ => {
                    let variable = variable.to_py(py);
                    let right = right.to_py(py);
                    match variable.add(right) {
                        Ok(variable) => Content::Py(PyContent {
                            content: variable,
                            at: self.argument.at,
                        }),
                        Err(_) => "".as_content(),
                    }
                }
            },
        ))
    }
}

impl ResolveFilter for CapfirstFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => content
                .resolve_string(py, template, context)?
                .map_content(|content| {
                    let mut chars = content.chars();
                    match chars.next() {
                        Some(first) => Cow::Owned(first.to_uppercase().chain(chars).collect()),
                        None => content,
                    }
                }),
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for CenterFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(content) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };
        let content = content.resolve_string(py, template, context)?;
        let arg = match self.argument.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(_) => {
                unreachable!("missing argument in context should already have raised")
            }
        };

        let size = arg.resolve_usize(self.argument.at, template_name, template.0)?;

        // Python's `str.center` counts characters, not bytes.
        let length = content.as_raw().chars().count();
        if size <= length {
            return Ok(ResolveContent::Content(Content::String(content)));
        }
        let round_up = size % 2 == 0 && length % 2 != 0;
        let right = if round_up {
            // If the size is even and the content length is odd, we need to adjust the centering
            (size - length).div_ceil(2)
        } else {
            (size - length) / 2
        };
        let left = size - length - right;

        Ok(ResolveContent::Content(content.map_content(|content| {
            let mut centered = String::with_capacity(content.len() + left + right);

            centered.push_str(&" ".repeat(left));
            centered.push_str(&content);
            centered.push_str(&" ".repeat(right));

            Cow::Owned(centered)
        })))
    }
}

fn cut(source: Cow<'_, str>, value: &str) -> String {
    source.replace(value, "")
}

impl ResolveFilter for CutFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(variable) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };

        let arg = match self.argument.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(_) => {
                unreachable!("missing argument in context should already have raised")
            }
        }
        .resolve_string_strict(
            py,
            template,
            context,
            self.argument.at.into(),
            template_name,
        )?
        .into_raw();

        let content_string = variable.resolve_string(py, template, context)?;
        let result = match content_string {
            ContentString::String(s) => ContentString::String(cut(s, &arg).into()),
            ContentString::HtmlSafe(s) => {
                let cut = cut(s, &arg).into();
                match arg.as_ref() {
                    ";" => ContentString::HtmlUnsafe(cut),
                    _ => ContentString::HtmlSafe(cut),
                }
            }
            ContentString::HtmlUnsafe(s) => ContentString::HtmlUnsafe(cut(s, &arg).into()),
        };

        Ok(ResolveContent::Content(Content::String(result)))
    }
}

impl ResolveFilter for DefaultFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        match variable {
            ResolveContent::Content(left)
                if left
                    .to_bool()
                    .map_err(|err| err.annotate(py, self.at, "here", template))? =>
            {
                Ok(ResolveContent::Content(left))
            }
            ResolveContent::Missing(_) | ResolveContent::Content(_) => self.argument.resolve(
                py,
                template,
                template_name,
                context,
                ResolveFailures::Raise,
                string_if_invalid,
            ),
        }
    }
}

impl ResolveFilter for DefaultIfNoneFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        match variable {
            ResolveContent::Content(Content::Py(PyContent {
                content: ref value, ..
            })) if value.is_none() => self.argument.resolve(
                py,
                template,
                template_name,
                context,
                ResolveFailures::Raise,
                string_if_invalid,
            ),
            ResolveContent::Content(left) => Ok(ResolveContent::Content(left)),
            ResolveContent::Missing(_) => Ok(ResolveContent::Content("".as_content())),
        }
    }
}

impl ResolveFilter for DateFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(value) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };

        let fmt = match &self.argument {
            Some(arg) => match arg.resolve(
                py,
                template,
                template_name,
                context,
                ResolveFailures::Raise,
                string_if_invalid,
            )? {
                ResolveContent::Content(content) => content,
                ResolveContent::Missing(_) => {
                    unreachable!("missing argument in context should already have raised")
                }
            }
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
            return Ok(ResolveContent::Content("".as_content()));
        }

        let date_format_fn = DATE_FORMAT.import(py, "django.utils.dateformat", "format")?;

        let formatted = match date_format_fn.call1((value, fmt)) {
            Ok(res) => res,
            Err(e) => {
                if e.is_instance_of::<pyo3::exceptions::PyAttributeError>(py) {
                    return Ok(ResolveContent::Content("".as_content()));
                }
                return Err(PyRenderError::PyErr(
                    e.annotate(py, self.at, "here", template),
                ));
            }
        };

        Ok(ResolveContent::Content(Content::Py(PyContent {
            content: formatted,
            at: self.at,
        })))
    }
}

impl ResolveFilter for DivisibleByFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(variable) = variable else {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "invalid literal for int() with base 10: 'None'",
            )
            .annotate(py, self.at, "here", template)
            .into());
        };

        if let Content::Py(PyContent {
            content: ref obj, ..
        }) = variable
            && obj.is_none()
        {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                    "int() argument must be a string, a bytes-like object or a real number, not 'NoneType'",
                )
                .annotate(py, self.at, "here", template)
                .into());
        }

        let right = match self.argument.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(_) => {
                unreachable!("missing argument in context should already have raised")
            }
        };

        let Some(right_val) = right.to_bigint() else {
            return Err(
                pyo3::exceptions::PyTypeError::new_err("Integer argument expected")
                    .annotate(py, self.argument.at, "here", template)
                    .into(),
            );
        };

        if right_val.is_zero() {
            return Err(pyo3::exceptions::PyZeroDivisionError::new_err(
                "Invalid divisibility check: cannot divide by zero",
            )
            .annotate(py, self.argument.at, "here", template)
            .into());
        }

        let Some(left_val) = variable.to_bigint() else {
            let value_str = variable.render(py, template, context)?;
            let msg = format!("invalid literal for int() with base 10: '{value_str}'");

            return Err(pyo3::exceptions::PyValueError::new_err(msg)
                .annotate(py, self.at, "here", template)
                .into());
        };

        Ok(ResolveContent::Content(Content::Bool(
            (left_val % right_val).is_zero(),
        )))
    }
}

impl ResolveFilter for EscapeFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        _context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        Ok(ResolveContent::Content(Content::String(
            ContentString::HtmlSafe(match variable {
                ResolveContent::Content(content) => match content {
                    Content::String(ContentString::HtmlSafe(content)) => content,
                    Content::String(content) => {
                        let mut encoded = String::new();
                        encode_quoted_attribute_to_string(content.as_raw(), &mut encoded);
                        Cow::Owned(encoded)
                    }
                    Content::Int(n) => Cow::Owned(n.to_string()),
                    Content::Float(n) => Cow::Owned(n.to_string()),
                    Content::Py(PyContent {
                        content: object,
                        at,
                    }) => {
                        let content = object
                            .str()
                            .map_err(|error| error.annotate(py, at, "here", template))?
                            .extract::<String>()?;
                        // Like Django's `conditional_escape`, leave safe strings alone.
                        #[allow(non_snake_case)]
                        let SafeData =
                            SAFEDATA.import(py, "django.utils.safestring", "SafeData")?;
                        if object
                            .is_instance(SafeData)
                            .map_err(|error| error.annotate(py, at, "here", template))?
                        {
                            Cow::Owned(content)
                        } else {
                            let mut encoded = String::new();
                            encode_quoted_attribute_to_string(&content, &mut encoded);
                            Cow::Owned(encoded)
                        }
                    }
                    Content::Bool(true) => Cow::Borrowed("True"),
                    Content::Bool(false) => Cow::Borrowed("False"),
                },
                ResolveContent::Missing(_) => Cow::Borrowed(""),
            }),
        )))
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
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => content
                .resolve_string(py, template, context)?
                .map_content(|content| Cow::Owned(escapejs(&content))),
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for ExternalFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let arg = match &self.argument {
            Some(arg) => arg
                .resolve(
                    py,
                    template,
                    template_name,
                    context,
                    ResolveFailures::Raise,
                    string_if_invalid,
                )?
                .maybe_content(),
            None => None,
        };
        let filter = self.filter.bind(py);
        let value = match arg {
            Some(arg) => filter.call1((variable.maybe_content(), arg))?,
            None => filter.call1((variable.maybe_content(),))?,
        };
        Ok(ResolveContent::Content(Content::Py(PyContent {
            content: value,
            at: self.at,
        })))
    }
}

impl ResolveFilter for ForceEscapeFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let variable = match variable {
            // We want to re-run the escape filter even if the content has already been resolved to safe HTML
            ResolveContent::Content(Content::String(ContentString::HtmlSafe(c))) => {
                ResolveContent::Content(Content::String(ContentString::String(c)))
            }
            other => other,
        };
        EscapeFilter.resolve(
            variable,
            py,
            template,
            template_name,
            context,
            string_if_invalid,
        )
    }
}

impl ResolveFilter for LastFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        _context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(content) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };

        let obj = content.to_py(py);

        match obj.get_item(-1) {
            Ok(last) => Ok(ResolveContent::Content(Content::Py(PyContent {
                content: last,
                at: self.at,
            }))),
            Err(err) => {
                if err.is_instance_of::<pyo3::exceptions::PyIndexError>(py) {
                    Ok(ResolveContent::Content("".as_content()))
                } else {
                    let error = err.annotate(py, self.at, "here", template);
                    Err(error.into())
                }
            }
        }
    }
}

impl ResolveFilter for LowerFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => content
                .resolve_string(py, template, context)?
                .map_content(|content| Cow::Owned(content.to_lowercase())),
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for LengthFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        _py: Python<'py>,
        _template: TemplateString<'t>,
        _template_name: &'t FileName,
        _context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let len = match variable {
            ResolveContent::Missing(_) => 0,
            ResolveContent::Content(Content::String(s)) => s.as_raw().chars().count(),
            ResolveContent::Content(Content::Py(PyContent { content: obj, .. })) => {
                obj.len().unwrap_or(0)
            }
            ResolveContent::Content(Content::Int(_) | Content::Float(_) | Content::Bool(_)) => 0,
        };

        Ok(ResolveContent::Content(Content::Int(
            num_bigint::BigInt::from(len),
        )))
    }
}

impl ResolveFilter for SafeFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        _context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        Ok(ResolveContent::Content(Content::String(
            ContentString::HtmlSafe(match variable {
                ResolveContent::Content(content) => match content {
                    Content::String(content) => content.into_raw(),
                    Content::Int(n) => Cow::Owned(n.to_string()),
                    Content::Float(n) => Cow::Owned(n.to_string()),
                    Content::Py(PyContent {
                        content: object,
                        at,
                    }) => {
                        let content = object
                            .str()
                            .map_err(|error| error.annotate(py, at, "here", template))?
                            .extract::<String>()?;
                        Cow::Owned(content)
                    }
                    Content::Bool(true) => Cow::Borrowed("True"),
                    Content::Bool(false) => Cow::Borrowed("False"),
                },
                ResolveContent::Missing(_) => Cow::Borrowed(""),
            }),
        )))
    }
}

/// Convert spaces or repeated dashes to single dashes.
///
/// Remove characters that aren't ascii alphanumerics, underscores, or hyphens.
/// Convert to lowercase. Also strip leading and trailing whitespace, dashes, and underscores.
///
/// See <https://github.com/django/django/blob/stable/5.2.x/django/utils/text.py#L453>
pub fn slugify(content: Cow<str>) -> Cow<str> {
    let mut slug = String::with_capacity(content.len());

    let mut prev_dash = false;
    let ascii_content = content
        .as_ref()
        .nfkd()
        .filter(char::is_ascii)
        .skip_while(|c| !c.is_ascii_alphanumeric());
    for c in ascii_content {
        if c.is_ascii_alphanumeric() || c == '_' {
            slug.push(c.to_ascii_lowercase());
            prev_dash = false;
        } else if (dtl_lexer::python_compat::is_whitespace(c) || c == '-') && !prev_dash {
            slug.push('-');
            prev_dash = true;
        }
    }
    slug.truncate(slug.trim_end_matches(['-', '_']).len());
    Cow::Owned(slug)
}

impl ResolveFilter for SlugifyFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        _context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => match content {
                Content::Py(PyContent { content, at }) => {
                    let slug = slugify(Cow::Owned(
                        content
                            .str()
                            .map_err(|error| error.annotate(py, at, "here", template))?
                            .extract::<String>()?,
                    ));
                    #[allow(non_snake_case)]
                    let SafeData = SAFEDATA.import(py, "django.utils.safestring", "SafeData")?;
                    match content
                        .is_instance(SafeData)
                        .map_err(|error| error.annotate(py, at, "here", template))?
                    {
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
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for TitleFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(content) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };
        let content_string = content.resolve_string(py, template, context)?;

        Ok(ResolveContent::Content(content_string.map_content(
            |content| {
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
            },
        )))
    }
}

impl ResolveFilter for UpperFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => {
                // Django's `upper` is not `is_safe`, so a safe input is escaped again.
                let content = match content.resolve_string(py, template, context)? {
                    ContentString::HtmlSafe(content) => ContentString::HtmlUnsafe(content),
                    content => content,
                };
                content.map_content(|content| Cow::Owned(content.to_uppercase()))
            }
            ResolveContent::Missing(_) => "".as_content(),
        };
        Ok(ResolveContent::Content(content))
    }
}

impl ResolveFilter for WordcountFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        _template_name: &'t FileName,
        context: &mut Context,
        _string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let content = match variable {
            ResolveContent::Content(content) => {
                let content_string = content.resolve_string(py, template, context)?;
                let word_count = content_string
                    .as_raw()
                    .split(dtl_lexer::python_compat::is_whitespace)
                    .filter(|word| !word.is_empty())
                    .count();
                Content::Int(word_count.into())
            }
            ResolveContent::Missing(_) => Content::Int(0.into()),
        };
        Ok(ResolveContent::Content(content))
    }
}

/// A run of `textwrap` whitespace or non-whitespace in a line.
#[derive(Clone, Copy)]
struct Chunk {
    start: usize,
    end: usize,
    len: usize,
}

impl Chunk {
    fn is_blank(&self, line: &str) -> bool {
        line[self.start..self.end]
            .chars()
            .all(dtl_lexer::python_compat::is_whitespace)
    }
}

/// Split a line into the chunks `textwrap.TextWrapper` works with.
struct Chunks<'t> {
    rest: &'t str,
    byte: usize,
}

impl Iterator for Chunks<'_> {
    type Item = Chunk;

    fn next(&mut self) -> Option<Self::Item> {
        let mut chars = self.rest.chars();
        let whitespace = python_compat::is_textwrap_whitespace(chars.next()?);
        let mut len = 1;
        let mut size = self.rest.len();
        for (index, c) in self.rest.char_indices().skip(1) {
            if python_compat::is_textwrap_whitespace(c) != whitespace {
                size = index;
                break;
            }
            len += 1;
        }
        let chunk = Chunk {
            start: self.byte,
            end: self.byte + size,
            len,
        };
        self.rest = &self.rest[size..];
        self.byte += size;
        Some(chunk)
    }
}

/// Build the lines of a wrapped line like `textwrap.TextWrapper` with the options Django uses.
///
/// See <https://github.com/python/cpython/blob/3.14/Lib/textwrap.py#L235>
struct WrappedLines<'t> {
    line: &'t str,
    width: usize,
    chunks: std::iter::Peekable<Chunks<'t>>,
    first_line: bool,
}

impl<'t> WrappedLines<'t> {
    fn new(line: &'t str, width: usize) -> Self {
        Self {
            line,
            width,
            chunks: Chunks {
                rest: line,
                byte: 0,
            }
            .peekable(),
            first_line: true,
        }
    }
}

impl<'t> Iterator for WrappedLines<'t> {
    type Item = &'t str;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            // drop leading whitespace, except on the first line
            if !self.first_line
                && let Some(chunk) = self.chunks.peek()
                && chunk.is_blank(self.line)
            {
                self.chunks.next();
            }
            let first = *self.chunks.peek()?;
            let mut line_len = 0;
            let mut last = None;
            let mut before_last = None;
            while let Some(chunk) = self
                .chunks
                .next_if(|chunk| line_len + chunk.len <= self.width)
            {
                line_len += chunk.len;
                before_last = last;
                last = Some(chunk);
            }
            // long words are not broken
            let mut last = match last {
                Some(last) => last,
                None => self.chunks.next()?,
            };
            // drop trailing whitespace
            if last.is_blank(self.line) {
                match before_last {
                    Some(chunk) => last = chunk,
                    None => continue,
                }
            }
            self.first_line = false;
            return Some(&self.line[first.start..last.end]);
        }
    }
}

/// A word-wrap function that preserves existing line breaks.
///
/// Preserve all white space except added line breaks consume the space on
/// which they break the line.
///
/// Don't wrap long words, thus the output text may have lines longer than ``width``.
///
/// See <https://github.com/django/django/blob/stable/5.2.x/django/utils/text.py#L40>
fn wordwrap(text: &str, width: usize) -> String {
    let mut result = String::with_capacity(text.len());

    for (i, line) in python_compat::splitlines(text).enumerate() {
        if i > 0 {
            result.push('\n');
        }

        let expanded = python_compat::expand_tabs(line);
        let mut wrapped = false;
        for (j, wrapped_line) in WrappedLines::new(&expanded, width).enumerate() {
            if j > 0 {
                result.push('\n');
            }
            result.push_str(wrapped_line);
            wrapped = true;
        }
        if !wrapped {
            // Line contains only whitespace that is dropped - preserve it
            result.push_str(line);
        }
    }
    if text.ends_with('\n') {
        result.push('\n');
    }

    result
}

impl ResolveFilter for WordwrapFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let ResolveContent::Content(content) = variable else {
            return Ok(ResolveContent::Content("".as_content()));
        };

        let text = content.resolve_string(py, template, context)?;

        let arg = match self.argument.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            ResolveContent::Content(content) => content,
            ResolveContent::Missing(_) => {
                unreachable!("missing argument in context should already have raised")
            }
        };

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

        let width = match arg.resolve_usize(self.argument.at, template_name, template.0) {
            Ok(w) => w,
            Err(PyRenderError::RenderError(RenderError::OverflowError { .. })) => usize::MAX,
            Err(e) => return Err(e),
        };

        let wrapped = wordwrap(text.as_raw(), width);
        Ok(ResolveContent::Content(
            text.map_content(|_| Cow::Owned(wrapped)),
        ))
    }
}

impl ResolveFilter for YesnoFilter {
    fn resolve<'t, 'py>(
        &self,
        variable: ResolveContent<'t, 'py>,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: StringIfInvalid<'t>,
    ) -> ResolveResult<'t, 'py> {
        let arg_string = match &self.argument {
            Some(arg) => {
                let arg_content = match arg.resolve(
                    py,
                    template,
                    template_name,
                    context,
                    ResolveFailures::Raise,
                    string_if_invalid,
                )? {
                    ResolveContent::Content(content) => content,
                    ResolveContent::Missing(_) => {
                        unreachable!("missing argument in context should already have raised")
                    }
                };
                arg_content
                    .resolve_string_strict(py, template, context, arg.at.into(), template_name)?
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
            ResolveContent::Content(Content::Py(PyContent {
                content: ref obj, ..
            })) if obj.is_none() => maybe,
            ResolveContent::Content(content) => match content.to_bool() {
                Ok(true) => yes,
                Ok(false) => no,
                Err(error) => {
                    let error = error.annotate(py, self.at, "when calling __bool__ here", template);
                    return Err(error.into());
                }
            },
            ResolveContent::Missing(_) => no,
        };

        Ok(ResolveContent::Content(result.to_string().into_content()))
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
    use crate::types::{Argument, ArgumentType, Text, Variable};

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

    use std::collections::HashMap;

    #[test]
    fn test_render_filter() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|default:'Bryony' }}");
            let variable = Variable::Variable((3, 4));
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

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ quotes|addslashes }}");
            let variable = Variable::Variable((3, 6));
            let filter = Filter {
                at: (10, 10),
                all_at: (3, 17),
                left: TagElement::Variable(variable),
                filter: FilterType::AddSlashes(AddSlashesFilter),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "Hello world");

            let context = PyDict::new(py);
            context.set_item("var", "").unwrap();
            let template_string = "{{ var|capfirst }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "");

            let context = PyDict::new(py);
            context.set_item("bar", "").unwrap();
            let template_string = "{{ var|capfirst }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "   hello   ");

            let context = PyDict::new(py);
            context.set_item("var", "django").unwrap();
            let template_string = "{{ var|center:'15' }}".to_string();
            let template = Template::new_from_string(py, template_string, engine.clone()).unwrap();
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "     django    ");

            let context = PyDict::new(py);
            context.set_item("var", "django").unwrap();
            let template_string = "{{ var|center:1 }}".to_string();
            let template = Template::new_from_string(py, template_string, engine).unwrap();
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "django");
        });
    }

    #[test]
    fn test_render_filter_center_no_argument_return_err() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let template_string = "{{ var|center }}".to_string();
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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

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
            let result = template
                .py_render(py, Some(context.into_any()), None)
                .unwrap();

            assert_eq!(result, "hello");
        });
    }

    #[test]
    fn test_render_filter_default() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|default:'Bryony' }}");
            let variable = Variable::Variable((3, 4));
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

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "Bryony");
        });
    }

    #[test]
    fn test_render_filter_default_integer() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ count|default:12}}");
            let variable = Variable::Variable((3, 5));
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

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "12");
        });
    }

    #[test]
    fn test_render_filter_default_float() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ count|default:3.5}}");
            let variable = Variable::Variable((3, 5));
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

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "3.5");
        });
    }

    #[test]
    fn test_render_filter_default_variable() {
        Python::initialize();

        Python::attach(|py| {
            let me = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("me".to_string(), me.unbind())]);
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|default:me}}");
            let variable = Variable::Variable((3, 4));
            let filter = Filter {
                at: (8, 7),
                all_at: (3, 11),
                left: TagElement::Variable(variable),
                filter: FilterType::Default(DefaultFilter::new(
                    Argument {
                        at: (16, 2),
                        argument_type: ArgumentType::Variable(Variable::Variable((16, 2))),
                    },
                    (8, 7),
                )),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "Lily");
        });
    }

    #[test]
    fn test_render_filter_lower() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Lily").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|lower }}");
            let variable = Variable::Variable((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Lower(LowerFilter),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "lily");
        });
    }

    #[test]
    fn test_render_filter_lower_missing_left() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|lower }}");
            let variable = Variable::Variable((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Lower(LowerFilter),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "");
        });
    }

    #[test]
    fn test_render_chained_filters() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|default:'Bryony'|lower }}");
            let variable = Variable::Variable((3, 4));
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

            let rendered = lower
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "bryony");
        });
    }

    #[test]
    fn test_render_filter_upper() {
        Python::initialize();

        Python::attach(|py| {
            let name = PyString::new(py, "Foo").into_any();
            let context = HashMap::from([("name".to_string(), name.unbind())]);
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|upper }}");
            let variable = Variable::Variable((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Upper(UpperFilter),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "FOO");
        });
    }

    #[test]
    fn test_render_filter_upper_missing_left() {
        Python::initialize();

        Python::attach(|py| {
            let context = HashMap::new();
            let mut context = Context::new(context, None, false, Vec::new());
            let template = TemplateString("{{ name|upper }}");
            let variable = Variable::Variable((3, 4));
            let filter = Filter {
                at: (8, 5),
                all_at: (3, 10),
                left: TagElement::Variable(variable),
                filter: FilterType::Upper(UpperFilter),
            };

            let rendered = filter
                .render(py, template, &FileName(None), &mut context, "".into())
                .unwrap();
            assert_eq!(rendered, "");
        });
    }

    #[test]
    fn test_wordwrap_matches_django_wrap() {
        use proptest::prelude::*;

        Python::initialize();
        let text_strategy = prop_oneof![
            "[a-z \t\n\r\u{b}\u{c}\u{1c}\u{1d}\u{1e}\u{85}\u{a0}\u{2028}\u{3000}é日]{0,60}",
            any::<String>(),
        ];
        proptest!(|(text in text_strategy, width in 1usize..30)| {
            Python::attach(|py| {
                let django_wrap = py
                    .import("django.utils.text")
                    .unwrap()
                    .getattr("wrap")
                    .unwrap();
                let expected: String = django_wrap.call1((&text, width)).unwrap().extract().unwrap();
                prop_assert_eq!(wordwrap(&text, width), expected);
                Ok(())
            })?;
        });
    }
}
