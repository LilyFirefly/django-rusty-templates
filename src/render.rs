pub mod common;
pub mod filters;
pub mod lorem;
pub mod tags;
pub mod types;

use std::borrow::Cow;
use std::path::PathBuf;

use pyo3::prelude::*;

use dtl_lexer::types::TemplateString;

use crate::error::PyRenderError;
use types::{Content, Context};

pub type ResolveResult<'t, 'py> = Result<Option<Content<'t, 'py>>, PyRenderError>;
pub type RenderResult<'t> = Result<Cow<'t, str>, PyRenderError>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FileName(pub Option<PathBuf>);

impl FileName {
    pub fn template_name(&self) -> Cow<'_, str> {
        match &self.0 {
            Some(filename) => filename.to_string_lossy(),
            None => Cow::Borrowed("<string template>"),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ResolveFailures {
    Raise,
    IgnoreVariableDoesNotExist,
}

/// Trait for resolving a template element into content suitable for
/// further processing by another template element.
trait Resolve {
    fn resolve<'t, 'py>(
        &self,
        py: Python<'py>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        failures: ResolveFailures,
        string_if_invalid: &'t str,
    ) -> ResolveResult<'t, 'py>;
}

/// Trait for rendering a template element into content suitable for
/// output in the completely processed template.
pub trait Render {
    fn render<'t>(
        &self,
        py: Python<'_>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: &'t str,
    ) -> RenderResult<'t>;
}

/// Trait for evaluating an expression in a boolean context
pub trait Evaluate {
    fn evaluate(
        &self,
        py: Python<'_>,
        template: TemplateString<'_>,
        template_name: &FileName,
        context: &mut Context,
        string_if_invalid: &str,
    ) -> Option<bool>;
}

impl<T> Evaluate for Option<T>
where
    T: Evaluate,
{
    fn evaluate(
        &self,
        py: Python<'_>,
        template: TemplateString<'_>,
        template_name: &FileName,
        context: &mut Context,
        string_if_invalid: &str,
    ) -> Option<bool> {
        match self {
            Some(inner) => inner.evaluate(py, template, template_name, context, string_if_invalid),
            None => Some(false),
        }
    }
}

/// All resolvable template elements can be rendered
impl<T> Render for T
where
    T: Resolve,
{
    fn render<'t>(
        &self,
        py: Python<'_>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: &'t str,
    ) -> RenderResult<'t> {
        match self.resolve(
            py,
            template,
            template_name,
            context,
            ResolveFailures::Raise,
            string_if_invalid,
        )? {
            Some(content) => Ok(content.render(py, template, context)?),
            None => Ok(string_if_invalid.into()),
        }
    }
}

impl<T> Render for Vec<T>
where
    T: Render,
{
    fn render<'t>(
        &self,
        py: Python<'_>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: &'t str,
    ) -> RenderResult<'t> {
        match self.len() {
            0 => Ok(Cow::Borrowed("")),
            1 => self[0].render(py, template, template_name, context, string_if_invalid),
            _ => Ok(Cow::Owned(
                self.iter()
                    .map(|node| {
                        node.render(py, template, template_name, context, string_if_invalid)
                    })
                    .collect::<Result<Vec<_>, _>>()?
                    .join(""),
            )),
        }
    }
}

impl<T> Render for Option<T>
where
    T: Render,
{
    fn render<'t>(
        &self,
        py: Python<'_>,
        template: TemplateString<'t>,
        template_name: &'t FileName,
        context: &mut Context,
        string_if_invalid: &'t str,
    ) -> RenderResult<'t> {
        Ok(match self {
            Some(inner) => inner.render(py, template, template_name, context, string_if_invalid)?,
            None => Cow::Borrowed(""),
        })
    }
}
