use std::borrow::Cow;
use std::ops::Deref;

#[derive(Clone, Copy)]
pub struct TemplateString<'t>(pub &'t str);

impl<'t> TemplateString<'t> {
    pub fn content(&self, at: (usize, usize)) -> &'t str {
        let (start, len) = at;
        &self.0[start..start + len]
    }
}

impl<'t> From<&'t str> for TemplateString<'t> {
    fn from(value: &'t str) -> Self {
        TemplateString(value)
    }
}

pub trait IntoTemplateString<'t> {
    fn into_template_string(self) -> TemplateString<'t>;
}
impl<'t> IntoTemplateString<'t> for &'t str {
    fn into_template_string(self) -> TemplateString<'t> {
        TemplateString(self)
    }
}
