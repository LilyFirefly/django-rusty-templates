use std::borrow::Cow;

/// The characters `textwrap` breaks lines on.
pub const fn is_textwrap_whitespace(c: char) -> bool {
    matches!(c, '\t' | '\n' | '\x0b' | '\x0c' | '\r' | ' ')
}

/// Split lines like Python's `str.splitlines`.
pub fn splitlines(text: &str) -> Splitlines<'_> {
    Splitlines { rest: text }
}

pub struct Splitlines<'t> {
    rest: &'t str,
}

impl<'t> Iterator for Splitlines<'t> {
    type Item = &'t str;

    fn next(&mut self) -> Option<Self::Item> {
        if self.rest.is_empty() {
            return None;
        }
        let mut chars = self.rest.char_indices().peekable();
        while let Some((index, c)) = chars.next() {
            let mut end = index + c.len_utf8();
            match c {
                '\r' => {
                    if let Some((_, '\n')) = chars.peek() {
                        end += 1;
                    }
                }
                '\n' | '\x0b' | '\x0c' | '\x1c' | '\x1d' | '\x1e' | '\u{85}' | '\u{2028}'
                | '\u{2029}' => {}
                _ => continue,
            }
            let line = &self.rest[..index];
            self.rest = &self.rest[end..];
            return Some(line);
        }
        let line = self.rest;
        self.rest = "";
        Some(line)
    }
}

/// Expand tabs like Python's `str.expandtabs`.
pub fn expand_tabs(line: &str) -> Cow<'_, str> {
    if !line.contains('\t') {
        return Cow::Borrowed(line);
    }
    let mut expanded = String::with_capacity(line.len() * 2);
    let mut column = 0;
    for c in line.chars() {
        if c == '\t' {
            let spaces = 8 - column % 8;
            expanded.extend(std::iter::repeat_n(' ', spaces));
            column += spaces;
        } else {
            expanded.push(c);
            column += 1;
        }
    }
    Cow::Owned(expanded)
}
