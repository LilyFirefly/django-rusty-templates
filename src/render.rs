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

#[derive(Clone, Debug, PartialEq)]
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
    ) -> Option<bool> {
        match self {
            Some(inner) => inner.evaluate(py, template, template_name, context),
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
    ) -> RenderResult<'t> {
        match self.resolve(py, template, template_name, context, ResolveFailures::Raise)? {
            Some(content) => Ok(content.render(py, template, context)?),
            None => Ok(Cow::Borrowed("")),
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
    ) -> RenderResult<'t> {
        match self.len() {
            0 => Ok(Cow::Borrowed("")),
            1 => self[0].render(py, template, template_name, context),
            _ => Ok(Cow::Owned(
                self.iter()
                    .map(|node| node.render(py, template, template_name, context))
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
    ) -> RenderResult<'t> {
        Ok(match self {
            Some(inner) => inner.render(py, template, template_name, context)?,
            None => Cow::Borrowed(""),
        })
    }
}
