use crate::types::{At, TemplateString};
use crate::{DelimitedToken, END_TAG_LEN, START_TAG_LEN};

enum EndTag {
    Variable,
    Tag,
    Comment,
}

#[derive(Debug, PartialEq, Eq)]
pub enum TokenType {
    Text,
    Variable,
    Tag,
    Comment,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Token {
    pub token_type: TokenType,
    pub at: At,
}

impl Token {
    fn text(at: At) -> Self {
        Self {
            at,
            token_type: TokenType::Text,
        }
    }

    fn variable(at: At) -> Self {
        Self {
            at,
            token_type: TokenType::Variable,
        }
    }

    fn tag(at: At) -> Self {
        Self {
            at,
            token_type: TokenType::Tag,
        }
    }

    fn comment(at: At) -> Self {
        Self {
            at,
            token_type: TokenType::Comment,
        }
    }
}

impl DelimitedToken for Token {
    fn trimmed_at(&self) -> At {
        if matches!(self.token_type, TokenType::Text) {
            self.at
        } else {
            let (start, len) = self.at;
            let start = start + START_TAG_LEN;
            let len = len - START_TAG_LEN - END_TAG_LEN;
            (start, len)
        }
    }
}

impl<'t> Token {
    pub fn content(&self, template: TemplateString<'t>) -> &'t str {
        template.content(self.trimmed_at())
    }
}

pub struct Lexer<'t> {
    template: TemplateString<'t>,
    rest: &'t str,
    byte: usize,
    verbatim: Option<&'t str>,
}

impl<'t> Lexer<'t> {
    pub fn new(template: TemplateString<'t>) -> Self {
        Self {
            template,
            rest: template.0,
            byte: 0,
            verbatim: None,
        }
    }

    fn lex_text(&mut self, skip: usize) -> Token {
        let rest = &self.rest[skip..];
        let next_tag = rest.find("{%");
        let next_variable = rest.find("{{");
        let next_comment = rest.find("{#");
        let next = [next_tag, next_variable, next_comment]
            .iter()
            .filter_map(|n| *n)
            .min();
        let len = next.map_or(self.rest.len(), |n| skip + n);
        self.rest = &self.rest[len..];
        let at = (self.byte, len);
        self.byte += len;
        Token::text(at)
    }

    fn lex_text_to_end(&mut self) -> Token {
        let len = self.rest.len();
        let at = (self.byte, len);
        self.byte += len;
        self.rest = "";
        Token::text(at)
    }

    fn lex_tag(&mut self, end_tag: EndTag) -> Token {
        let end_str = match end_tag {
            EndTag::Variable => "}}",
            EndTag::Tag => "%}",
            EndTag::Comment => "#}",
        };
        // This can be removed if https://code.djangoproject.com/ticket/35899 lands
        let line = self
            .rest
            .split_once('\n')
            .map_or(self.rest, |(line, _)| line);
        let Some(n) = line[START_TAG_LEN..].find(end_str) else {
            // Not closed on this line: treat the `{` as text and retry from the next character.
            return self.lex_text(1);
        };
        let len = START_TAG_LEN + n + end_str.len();
        self.rest = &self.rest[len..];

        let at = (self.byte, len);
        self.byte += len;
        match end_tag {
            EndTag::Variable => Token::variable(at),
            EndTag::Tag => Token::tag(at),
            EndTag::Comment => Token::comment(at),
        }
    }

    fn lex_verbatim(&mut self, verbatim: &'t str) -> Token {
        let verbatim = verbatim.trim();
        self.verbatim = None;

        let mut index = 0;
        loop {
            let Some(start) = self.rest[index..].find("{%").map(|n| index + n) else {
                return self.lex_text_to_end();
            };
            let inner_start = start + START_TAG_LEN;
            let Some(end) = self.rest[inner_start..].find("%}").map(|n| inner_start + n) else {
                return self.lex_text_to_end();
            };
            let inner = &self.rest[inner_start..end];
            if inner.contains('\n') {
                index = inner_start;
                continue;
            }
            if inner.trim().strip_prefix("end") != Some(verbatim) {
                index = end + END_TAG_LEN;
                continue;
            }
            if start == 0 {
                // Return the endverbatim tag since we have no text
                let tag_len = end + END_TAG_LEN;
                let at = (self.byte, tag_len);
                self.byte += tag_len;
                self.rest = &self.rest[tag_len..];
                return Token::tag(at);
            }
            self.rest = &self.rest[start..];
            let at = (self.byte, start);
            self.byte += start;
            return Token::text(at);
        }
    }
}

impl Iterator for Lexer<'_> {
    type Item = Token;

    fn next(&mut self) -> Option<Self::Item> {
        if self.rest.is_empty() {
            return None;
        }
        Some(match self.verbatim {
            None => match self.rest.get(..START_TAG_LEN) {
                Some("{{") => self.lex_tag(EndTag::Variable),
                Some("{%") => {
                    let tag = self.lex_tag(EndTag::Tag);
                    if let Token {
                        token_type: TokenType::Tag,
                        ..
                    } = tag
                    {
                        let verbatim = tag.content(self.template).trim();
                        if verbatim == "verbatim" || verbatim.starts_with("verbatim ") {
                            self.verbatim = Some(verbatim);
                        }
                    }
                    tag
                }
                Some("{#") => self.lex_tag(EndTag::Comment),
                _ => self.lex_text(0),
            },
            Some(verbatim) => self.lex_verbatim(verbatim),
        })
    }
}
#[cfg(test)]
mod tests {
    use super::*;

    fn contents<'t>(template: impl Into<TemplateString<'t>>, tokens: Vec<Token>) -> Vec<&'t str> {
        let template = template.into();
        tokens.iter().map(|t| t.content(template)).collect()
    }

    #[test]
    fn test_lex_empty() {
        let template = "";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![]);
    }

    #[test]
    fn test_lex_text() {
        let template = "Just some text";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::text((0, 14))]);
        assert_eq!(contents(template, tokens), vec![template]);
    }

    #[test]
    fn test_lex_text_whitespace() {
        let template = "    ";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::text((0, 4))]);
        assert_eq!(contents(template, tokens), vec![template]);
    }

    #[test]
    fn test_lex_comment() {
        let template = "{# comment #}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::comment((0, 13))]);
        assert_eq!(contents(template, tokens), vec![" comment "]);
    }

    #[test]
    fn test_lex_variable() {
        let template = "{{ foo.bar|title }}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::variable((0, 19))]);
        assert_eq!(contents(template, tokens), vec![" foo.bar|title "]);
    }

    #[test]
    fn test_lex_tag() {
        let template = "{% for foo in bar %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::tag((0, 20))]);
        assert_eq!(contents(template, tokens), vec![" for foo in bar "]);
    }

    #[test]
    fn test_lex_incomplete_comment() {
        let template = "{# comment #";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::text((0, 12))]);
        assert_eq!(contents(template, tokens), vec![template]);
    }

    #[test]
    fn test_lex_incomplete_variable() {
        let template = "{{ foo.bar|title }";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::text((0, 18))]);
        assert_eq!(contents(template, tokens), vec![template]);
    }

    #[test]
    fn test_lex_incomplete_tag() {
        let template = "{% for foo in bar %";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::text((0, 19))]);
        assert_eq!(contents(template, tokens), vec![template]);
    }

    #[test]
    fn test_django_example() {
        let template = "text\n{% if test %}{{ varvalue }}{% endif %}{#comment {{not a var}} {%not a block%} #}end text";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::text((0, 5)),
                Token::tag((5, 13)),
                Token::variable((18, 14)),
                Token::tag((32, 11)),
                Token::comment((43, 42)),
                Token::text((85, 8)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![
                "text\n",
                " if test ",
                " varvalue ",
                " endif ",
                "comment {{not a var}} {%not a block%} ",
                "end text",
            ]
        );
    }

    #[test]
    fn test_verbatim_with_variable() {
        let template = "{% verbatim %}{{bare   }}{% endverbatim %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 14)),
                Token::text((14, 11)),
                Token::tag((25, 17)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![" verbatim ", "{{bare   }}", " endverbatim "]
        );
    }

    #[test]
    fn test_verbatim_with_tag() {
        let template = "{% verbatim %}{% endif %}{% endverbatim %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 14)),
                Token::text((14, 11)),
                Token::tag((25, 17)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![" verbatim ", "{% endif %}", " endverbatim "]
        );
    }

    #[test]
    fn test_verbatim_with_verbatim_tag() {
        let template = "{% verbatim %}It's the {% verbatim %} tag{% endverbatim %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 14)),
                Token::text((14, 27)),
                Token::tag((41, 17)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![" verbatim ", "It's the {% verbatim %} tag", " endverbatim "]
        );
    }

    #[test]
    fn test_verbatim_nested() {
        let template = "{% verbatim %}{% verbatim %}{% endverbatim %}{% endverbatim %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 14)),
                Token::text((14, 14)),
                Token::tag((28, 17)),
                Token::tag((45, 17)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![
                " verbatim ",
                "{% verbatim %}",
                " endverbatim ",
                " endverbatim ",
            ]
        );
    }

    #[test]
    fn test_verbatim_adjacent() {
        let template = "{% verbatim %}{% endverbatim %}{% verbatim %}{% endverbatim %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 14)),
                Token::tag((14, 17)),
                Token::tag((31, 14)),
                Token::tag((45, 17)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![" verbatim ", " endverbatim ", " verbatim ", " endverbatim "]
        );
    }

    #[test]
    fn test_verbatim_special() {
        let template =
            "{% verbatim special %}Don't {% endverbatim %} just yet{% endverbatim special %}";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(
            tokens,
            vec![
                Token::tag((0, 22)),
                Token::text((22, 32)),
                Token::tag((54, 25)),
            ]
        );
        assert_eq!(
            contents(template, tokens),
            vec![
                " verbatim special ",
                "Don't {% endverbatim %} just yet",
                " endverbatim special ",
            ]
        );
    }

    #[test]
    fn test_verbatim_open_tag() {
        let template = "{% verbatim %}Don't {% ";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::tag((0, 14)), Token::text((14, 9))]);
        assert_eq!(contents(template, tokens), vec![" verbatim ", "Don't {% "]);
    }

    #[test]
    fn test_verbatim_no_tag() {
        let template = "{% verbatim %}Don't end verbatim";
        let lexer = Lexer::new(template.into());
        let tokens: Vec<_> = lexer.collect();
        assert_eq!(tokens, vec![Token::tag((0, 14)), Token::text((14, 18))]);
        assert_eq!(
            contents(template, tokens),
            vec![" verbatim ", "Don't end verbatim"]
        );
    }

    #[test]
    fn test_trimmed_at_doesnt_panic() {
        assert_eq!(Token::text((34, 1)).trimmed_at(), (34, 1));
        assert_eq!(Token::text((34, 20)).trimmed_at(), (34, 20));
        assert_eq!(Token::tag((34, 5)).trimmed_at(), (36, 1));
        assert_eq!(Token::variable((34, 5)).trimmed_at(), (36, 1));
        assert_eq!(Token::comment((34, 5)).trimmed_at(), (36, 1));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    fn arb_template() -> impl Strategy<Value = String> {
        // Need a custom strategy because uniformly random strings would almost never contain a closed tag.
        // Simplest fragments first, because shrinking goes toward the start of the list.
        // See https://altsysrq.github.io/proptest-book/proptest/tutorial/shrinking-basics.html
        let fragment = prop::sample::select(vec![
            "x",
            "é",
            " ",
            "\n",
            "{",
            "}",
            "%",
            "#",
            "{{",
            "}}",
            "{%",
            "%}",
            "{#",
            "#}",
            "{% verbatim %}",
            "{% endverbatim %}",
            "{% verbatim x %}",
            "{% endverbatim x %}",
        ]);
        prop::collection::vec(fragment, 0..=40).prop_map(|fragments| fragments.concat())
    }

    fn lex(template: &str) -> Vec<Token> {
        Lexer::new(template.into()).collect()
    }

    // A tag is an opener, then its first closer on the same line.
    fn tag_at(template: &str, start: usize) -> Option<Token> {
        let line = template.get(start..)?.split('\n').next()?;
        let (token_type, closer) = match line.get(..START_TAG_LEN)? {
            "{%" => (TokenType::Tag, "%}"),
            "{{" => (TokenType::Variable, "}}"),
            "{#" => (TokenType::Comment, "#}"),
            _ => return None,
        };
        let content_len = line[START_TAG_LEN..].find(closer)?;
        let at = (start, START_TAG_LEN + content_len + END_TAG_LEN);
        Some(Token { token_type, at })
    }

    proptest! {
        #![proptest_config(ProptestConfig {
            timeout: 1000, // See https://altsysrq.github.io/proptest-book/proptest/forking.html
            ..ProptestConfig::with_cases(4096)
        })]

        #[test]
        fn tokens_are_contiguous_non_empty_and_cover_the_template(template in arb_template()) {
            let mut end = 0;
            for token in lex(&template) {
                let (start, len) = token.at;
                prop_assert_eq!(start, end);
                prop_assert!(len > 0);
                end += len;
            }
            prop_assert_eq!(end, template.len());
        }

        #[test]
        fn non_text_token_is_the_tag_at_its_start(template in arb_template()) {
            for token in lex(&template) {
                if token.token_type != TokenType::Text {
                    prop_assert_eq!(tag_at(&template, token.at.0), Some(token));
                }
            }
        }

        #[test]
        fn no_tag_starts_inside_a_text_token_outside_verbatim(template in arb_template()) {
            let mut in_verbatim = false;
            for token in lex(&template) {
                if token.token_type != TokenType::Text {
                    let content = token.content(template.as_str().into()).trim();
                    in_verbatim = token.token_type == TokenType::Tag
                        && (content == "verbatim" || content.starts_with("verbatim "));
                } else if !in_verbatim {
                    let (start, len) = token.at;
                    for at in start..start + len {
                        prop_assert_eq!(tag_at(&template, at), None);
                    }
                }
            }
        }

        #[test]
        fn verbatim_block_content_is_a_single_text_token(content in arb_template()) {
            let open = "{% verbatim block %}";
            // The newline keeps an unclosed `{%` in the content from swallowing the end tag.
            let text = format!("{content}\n");
            let close = "{% endverbatim block %}";
            let template = format!("{open}{text}{close}");
            let expected = [
                Token::tag((0, open.len())),
                Token::text((open.len(), text.len())),
                Token::tag((open.len() + text.len(), close.len())),
            ];
            prop_assert_eq!(lex(&template), expected);
        }
    }
}
