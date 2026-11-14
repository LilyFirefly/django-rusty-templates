import pytest
from inline_snapshot import snapshot


@pytest.mark.parametrize(
    "template, expected",
    [
        ("{% verbatim %}{{ a }}{% if %}{% endverbatim %}", "{{ a }}{% if %}"),
        ("{% verbatim %}{% endverbatim %}", ""),
        ("{% verbatim %}{% verbatim %}{% endverbatim %}", "{% verbatim %}"),
        (
            "{% verbatim x %}{% endverbatim %}{% endverbatim x %}{{ a }}",
            "{% endverbatim %}1",
        ),
        ("{% verbatim %}{% aaé %}{% endverbatim %}", "{% aaé %}"),
        ("{% verbatim %}{% xyzverbatim %}{% endverbatim %}", "{% xyzverbatim %}"),
    ],
)
def test_verbatim(assert_render, template, expected):
    assert_render(template=template, context={"a": 1}, expected=expected)


def test_missing_endverbatim(assert_parse_error):
    template = "{% verbatim %}{{ a }}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'verbatim'. Looking for one of: endverbatim."
    )
    rusty_message = snapshot("""\
  × Unclosed 'verbatim' tag. Looking for one of: endverbatim
   ╭────
 1 │ {% verbatim %}{{ a }}
   · ───────┬──────
   ·        ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )
