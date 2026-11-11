use miette::{Diagnostic, LabeledSpan, NamedSource, SourceSpan, miette};
use pyo3::exceptions::{PyKeyError, PyOverflowError, PyValueError};
use pyo3::prelude::*;
use thiserror::Error;

use crate::path::RelativePathError;
use crate::template::django_rusty_templates::{
    TemplateDoesNotExist, TemplateSyntaxError, VariableDoesNotExist, WithSourceCode,
};
use dtl_lexer::types::{At, TemplateString};

#[derive(Error, Debug)]
pub enum PyRenderError {
    #[error(transparent)]
    PyErr(#[from] PyErr),
    #[error(transparent)]
    RenderError(#[from] RenderError),
}

impl PyRenderError {
    pub fn try_into_render_error(self) -> PyResult<RenderError> {
        match self {
            Self::RenderError(err) => Ok(err),
            Self::PyErr(err) => Err(err),
        }
    }
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Couldn't convert argument ({argument}) to integer")]
pub struct InvalidArgumentInteger {
    pub argument: String,
    #[label("argument")]
    pub argument_at: SourceSpan,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Couldn't convert float ({argument}) to integer")]
pub struct InvalidArgumentFloat {
    pub argument: String,
    #[label("here")]
    pub argument_at: SourceSpan,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("String argument expected")]
pub struct InvalidArgumentString {
    #[label("here")]
    pub argument_at: SourceSpan,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Integer {argument} is too large")]
pub struct OverflowError {
    pub argument: String,
    #[label("here")]
    pub argument_at: SourceSpan,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Failed lookup for key [{key}] in {object}")]
pub struct ArgumentDoesNotExist {
    pub key: String,
    pub object: String,
    #[label("key")]
    pub key_at: SourceSpan,
    #[label("{object}")]
    pub object_at: Option<SourceSpan>,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Need {expected_count} values to unpack; got {actual_count}.")]
pub struct TupleUnpackError {
    pub expected_count: usize,
    pub actual_count: usize,
    #[label("unpacked here")]
    pub expected_at: SourceSpan,
    #[label("from here")]
    pub actual_at: SourceSpan,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("Failed lookup for key [{key}] in {object}")]
pub struct InnerVariableDoesNotExist {
    pub key: String,
    pub object: String,
    #[label("key")]
    pub key_at: SourceSpan,
    #[label("{object}")]
    pub object_at: Option<SourceSpan>,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum RenderError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    RelativePathError(#[from] RelativePathError),
    #[error(transparent)]
    #[diagnostic(transparent)]
    InvalidArgumentInteger(Box<InvalidArgumentInteger>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    InvalidArgumentFloat(Box<InvalidArgumentFloat>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    InvalidArgumentString(Box<InvalidArgumentString>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    OverflowError(Box<OverflowError>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    ArgumentDoesNotExist(Box<ArgumentDoesNotExist>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    TupleUnpackError(Box<TupleUnpackError>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    VariableDoesNotExist(Box<InnerVariableDoesNotExist>),
}

impl RenderError {
    pub fn into_pyerr(self, template: impl miette::SourceCode + 'static) -> PyErr {
        match self {
            Self::RelativePathError(_) => {
                TemplateSyntaxError::with_source_code(self.into(), template)
            }
            Self::VariableDoesNotExist { .. } | Self::ArgumentDoesNotExist { .. } => {
                VariableDoesNotExist::with_source_code(self.into(), template)
            }
            Self::InvalidArgumentInteger { .. }
            | Self::InvalidArgumentString { .. }
            | Self::TupleUnpackError { .. } => {
                PyValueError::with_source_code(self.into(), template)
            }
            Self::OverflowError { .. } | Self::InvalidArgumentFloat { .. } => {
                PyOverflowError::with_source_code(self.into(), template)
            }
        }
    }
}

#[pyclass]
struct KeyErrorMessage {
    message: String,
}

#[pymethods]
impl KeyErrorMessage {
    fn __repr__(&self) -> &str {
        &self.message
    }
}

pub trait AnnotatePyErr {
    fn annotate(self, py: Python<'_>, at: At, label: &str, template: TemplateString<'_>) -> Self;
}

impl AnnotatePyErr for PyErr {
    fn annotate(self, py: Python<'_>, at: At, label: &str, template: TemplateString<'_>) -> Self {
        let error = self.value(py);
        let message = miette!(labels = vec![LabeledSpan::at(at, label)], "{}", &error)
            .with_source_code(template.0.to_string());
        if self.is_instance_of::<PyKeyError>(py) {
            let message = format!("{message:?}");
            // Python converts the message to `repr(message)` for KeyError.
            // When annotating, this is unhelpful, so we work around this by defining a custom
            // `__repr__` that returns the message exactly as we want it.
            // https://github.com/python/cpython/blob/43573028c6ae21c66c118b8bae866c8968b87b68/Objects/exceptions.c#L2946-L2954
            let message = KeyErrorMessage { message };
            PyKeyError::new_err((message,))
        } else if self.is_instance_of::<TemplateDoesNotExist>(py) {
            let args = (
                format!("{message:?}"),
                error
                    .getattr("tried")
                    .expect("TemplateDoesNotExist should have a 'tried' attribute")
                    .unbind(),
                error
                    .getattr("backend")
                    .expect("TemplateDoesNotExist should have a 'backend' attribute")
                    .unbind(),
                error
                    .getattr("chain")
                    .expect("TemplateDoesNotExist should have a 'chain' attribute")
                    .unbind(),
            );
            let err_type = self.get_type(py);
            Self::from_type(err_type, args)
        } else {
            let err_type = self.get_type(py);
            Self::from_type(err_type, format!("{message:?}"))
        }
    }
}
