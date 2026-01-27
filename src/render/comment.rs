use std::borrow::Cow;

pub fn render_comment() -> Cow<'static, str> {
    Cow::Borrowed("")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_comment() {
        assert_eq!(render_comment(), "");
    }
}
