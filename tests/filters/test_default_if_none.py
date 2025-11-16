import pytest
from django.template.base import VariableDoesNotExist


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(None, "default_value", id="none_value"),
        pytest.param("", "", id="empty_string"),
        pytest.param(0, "0", id="zero"),
        pytest.param(False, "False", id="false"),
        pytest.param("actual_value", "actual_value", id="string_value"),
        pytest.param(42, "42", id="integer_value"),
        pytest.param(3.14, "3.14", id="float_value"),
        pytest.param(True, "True", id="true_value"),
        pytest.param([], "[]", id="empty_list"),
        pytest.param({}, "{}", id="empty_dict"),
    ],
)
def test_default_if_none_with_various_values(assert_render, value, expected):
    template = "{{ value|default_if_none:'default_value' }}"
    assert_render(template=template, context={"value": value}, expected=expected)


def test_default_if_none_with_missing_variable(assert_render):
    template = "{{ missing|default_if_none:'default' }}"
    assert_render(template=template, context={}, expected="")


@pytest.mark.parametrize(
    "template,expected",
    [
        pytest.param(
            "{{ value|default_if_none:'DEFAULT'|lower }}", "default", id="chained_lower"
        ),
        pytest.param(
            "{{ value|default_if_none:'default'|upper }}", "DEFAULT", id="chained_upper"
        ),
        pytest.param(
            "{{ value|default_if_none:'<b>default</b>'|safe }}",
            "<b>default</b>",
            id="chained_safe",
        ),
    ],
)
def test_default_if_none_chained_filters(assert_render, template, expected):
    assert_render(template=template, context={"value": None}, expected=expected)


def test_default_if_none_preserves_html_safe_value(assert_render):
    assert_render(
        template="{{ value|safe|default_if_none:'default' }}",
        context={"value": "<b>safe</b>"},
        expected="<b>safe</b>",
    )


def test_default_if_none_with_forloop_variable(assert_render):
    template = "{% for x in items %}{{ x|default_if_none:forloop.counter }}{% endfor %}"
    assert_render(
        template=template, context={"items": [None, "a", None]}, expected="1a3"
    )


def test_default_if_none_missing_argument(assert_parse_error):
    template = "{{ value|default_if_none }}"
    django_message = "default_if_none requires 2 arguments, 1 provided"
    rusty_message = """\
  × Expected an argument
   ╭────
 1 │ {{ value|default_if_none }}
   ·          ───────┬───────
   ·                 ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_default_if_none_missing_variable_argument(assert_render_error):
    django_message = "Failed lookup for key [missing] in [{'True': True, 'False': False, 'None': None}, {'value': None}]"
    rusty_message = """\
  × Failed lookup for key [missing] in {"False": False, "None": None, "True":
  │ True, "value": None}
   ╭────
 1 │ {{ value|default_if_none:missing }}
   ·                          ───┬───
   ·                             ╰── key
   ╰────
"""
    assert_render_error(
        template="{{ value|default_if_none:missing }}",
        context={"value": None},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )
