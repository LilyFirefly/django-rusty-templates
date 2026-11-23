/// Whitespace as Python's `str.strip` and `\s` see it.
pub fn is_whitespace(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\x1c'..='\x1f')
}

/// `str.strip` with no argument.
pub fn trim(s: &str) -> &str {
    s.trim_matches(is_whitespace)
}

/// `str.lstrip` with no argument.
pub fn trim_start(s: &str) -> &str {
    s.trim_start_matches(is_whitespace)
}

/// `str.rstrip` with no argument.
pub fn trim_end(s: &str) -> &str {
    s.trim_end_matches(is_whitespace)
}

pub trait NextChar {
    fn next_whitespace(&self) -> usize;
    fn next_non_whitespace(&self) -> usize;
}

impl NextChar for str {
    fn next_whitespace(&self) -> usize {
        self.find(is_whitespace).unwrap_or(self.len())
    }

    fn next_non_whitespace(&self) -> usize {
        self.find(|c| !is_whitespace(c)).unwrap_or(self.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_whitespace_matches_str_isspace() {
        // ''.join(c for c in map(chr, range(0x110000)) if c.isspace())
        let expected = "\t\n\x0b\x0c\r\x1c\x1d\x1e\x1f \u{85}\u{a0}\u{1680}\u{2000}\u{2001}\u{2002}\u{2003}\u{2004}\u{2005}\u{2006}\u{2007}\u{2008}\u{2009}\u{200a}\u{2028}\u{2029}\u{202f}\u{205f}\u{3000}";
        let whitespace: String = ('\0'..=char::MAX).filter(|&c| is_whitespace(c)).collect();
        assert_eq!(whitespace, expected);
    }
}
