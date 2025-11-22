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
