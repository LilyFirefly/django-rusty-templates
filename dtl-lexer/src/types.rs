pub type At = (usize, usize);

#[derive(Clone, Copy)]
pub struct TemplateString<'t>(pub &'t str);

impl<'t> TemplateString<'t> {
    pub fn content(&self, at: At) -> &'t str {
        let (start, len) = at;
        &self.0[start..start + len]
    }
}

impl<'t> From<&'t str> for TemplateString<'t> {
    fn from(value: &'t str) -> Self {
        TemplateString(value)
    }
}

impl<'t> std::fmt::Display for TemplateString<'t> {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> Result<(), std::fmt::Error> {
        write!(f, "{}", self.0)
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

pub struct PartsIterator<'t> {
    variable: &'t str,
    start: usize,
}

impl<'t> PartsIterator<'t> {
    pub fn new(template: TemplateString<'t>, at: At) -> Self {
        let start = at.0;
        let variable = template.content(at);
        Self { variable, start }
    }
}

impl<'t> Iterator for PartsIterator<'t> {
    type Item = (&'t str, At);

    fn next(&mut self) -> Option<Self::Item> {
        if self.variable.is_empty() {
            return None;
        }

        match self.variable.find('.') {
            Some(index) => {
                let part = &self.variable[..index];
                let at = (self.start, index);
                self.start += index + 1;
                self.variable = &self.variable[index + 1..];
                Some((part, at))
            }
            None => {
                let part = self.variable;
                self.variable = "";
                Some((part, (self.start, part.len())))
            }
        }
    }
}
