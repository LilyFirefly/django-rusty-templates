import pytest

from tests.utils import BrokenDunderStr


@pytest.mark.parametrize(
    "var,expected",
    [
        pytest.param("", "", id="empty"),
        pytest.param("hello world", "Hello World", id="basic"),
        pytest.param("Hello World", "Hello World", id="already_titled"),
        pytest.param("hELLo WoRLd", "Hello World", id="mixed_case"),
        pytest.param("HELLO WORLD", "Hello World", id="uppercase"),
        pytest.param("hello", "Hello", id="single_word"),
        # Special chars
        pytest.param("hello-world", "Hello-World", id="hyphen"),
        pytest.param("hello_world", "Hello_World", id="underscore"),
        pytest.param("hello.world", "Hello.World", id="period"),
        pytest.param("hello/world", "Hello/World", id="slash"),
        # Whitespace
        pytest.param("hello  world", "Hello  World", id="double_space"),
        pytest.param("hello\tworld", "Hello\tWorld", id="tab"),
        pytest.param("hello\nworld", "Hello\nWorld", id="newline"),
        pytest.param(" hello world ", " Hello World ", id="leading_trailing_space"),
        # Apostrophes
        pytest.param(
            "they're bill's friends from the UK",
            "They're Bill's Friends From The Uk",
            id="apostrophes",
        ),
        pytest.param("it's a nice day", "It's A Nice Day", id="its"),
        pytest.param("don't stop", "Don't Stop", id="dont"),
        pytest.param("JOE'S CRAB SHACK", "Joe's Crab Shack", id="caps"),
        # Digits
        pytest.param("2 apples", "2 Apples", id="digit_start"),
        pytest.param("1st place", "1st Place", id="digit_with_letters"),
        pytest.param("123abc", "123abc", id="digits_then_letters"),
        pytest.param(
            "555 WEST 53RD STREET", "555 West 53rd Street", id="street_number"
        ),
        # Unicodes
        pytest.param("café résumé", "Café Résumé", id="accented"),
        pytest.param("über", "Über", id="umlaut"),
        pytest.param("naïve", "Naïve", id="diaeresis"),
        pytest.param("hello 👋", "Hello 👋", id="emoji"),
        # Unexpected type
        pytest.param(123, "123", id="integer"),
        pytest.param(3.14, "3.14", id="float"),
        pytest.param(True, "True", id="bool_true"),
        pytest.param(False, "False", id="bool_false"),
        pytest.param("<b>hello world</b>", "<B>Hello World</B>", id="html"),
        pytest.param(None, "None", id="none"),
    ],
)
def test_title_basic(assert_render, var, expected):
    template = "{% autoescape off %}{{ var|title }}{% endautoescape %}"
    assert_render(template=template, context={"var": var}, expected=expected)


@pytest.mark.parametrize(
    "var,expected",
    [
        pytest.param(
            "they're bill's friends from the UK",
            "They&#x27;re Bill&#x27;s Friends From The Uk",
            id="apostrophes",
        ),
        pytest.param("it's a nice day", "It&#x27;s A Nice Day", id="its"),
        pytest.param("don't stop", "Don&#x27;t Stop", id="dont"),
        pytest.param("JOE'S CRAB SHACK", "Joe&#x27;s Crab Shack", id="caps"),
        pytest.param("<b>hello world</b>", "&lt;B&gt;Hello World&lt;/B&gt;", id="html"),
    ],
)
def test_title_with_autoescape(assert_render, var, expected):
    """Test that title filter properly escapes HTML and apostrophes when autoescape is on."""
    template = "{% autoescape on %}{{ var|title }}{% endautoescape %}"
    assert_render(template=template, context={"var": var}, expected=expected)


def test_title_undefined(assert_render):
    template = "{{ var|title }}"
    assert_render(template=template, context={}, expected="")


def test_title_chained_with_upper(assert_render):
    template = "{{ var|upper|title }}"
    var = "hello world"
    expected = "Hello World"
    assert_render(template=template, context={"var": var}, expected=expected)


def test_title_chained_with_lower(assert_render):
    template = "{{ var|lower|title }}"
    var = "HELLO WORLD"
    expected = "Hello World"
    assert_render(template=template, context={"var": var}, expected=expected)


def test_title_with_argument_error(assert_parse_error):
    template = "{{ var|title:arg }}"
    django_message = "title requires 1 arguments, 2 provided"
    rusty_message = """\
  × title filter does not take an argument
   ╭────
 1 │ {{ var|title:arg }}
   ·              ─┬─
   ·               ╰── unexpected argument
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_title_invalid_str_method(assert_render_error):
    broken = BrokenDunderStr()
    assert_render_error(
        template="{{ broken|title }}",
        context={"broken": broken},
        exception=ZeroDivisionError,
        django_message="division by zero",
        rusty_message="division by zero",
    )
