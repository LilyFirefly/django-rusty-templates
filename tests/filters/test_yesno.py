import pytest
from django.template import engines
from django.utils.translation import override

from tests.utils import BrokenDunderHtml, BrokenDunderBool


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "yes"),
        (False, "no"),
        (None, "maybe"),
        (1, "yes"),
        (0, "no"),
        (-1, "yes"),
        (1.5, "yes"),
        (0.0, "no"),
        ("hello", "yes"),
        ("", "no"),
        ([], "no"),
        ([1, 2, 3], "yes"),
    ],
)
def test_yesno_truthy_falsy(assert_render, value, expected):
    assert_render("{{ value|yesno }}", {"value": value}, expected)


def test_yesno_missing_variable(assert_render):
    assert_render("{{ value|yesno }}", {}, "no")


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "certainly"),
        (False, "get out of town"),
        (None, "perhaps"),
    ],
)
def test_yesno_three_arguments(assert_render, value, expected):
    assert_render(
        "{{ value|yesno:'certainly,get out of town,perhaps' }}",
        {"value": value},
        expected,
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "certainly"),
        (False, "get out of town"),
        (None, "get out of town"),
    ],
)
def test_yesno_two_arguments(assert_render, value, expected):
    assert_render(
        "{{ value|yesno:'certainly,get out of town' }}",
        {"value": value},
        expected,
    )


def test_yesno_with_variable_argument(assert_render):
    assert_render(
        "{{ value|yesno:choices }}",
        {"value": True, "choices": "affirmative,negative,unknown"},
        "affirmative",
    )


def test_yesno_chained_with_other_filters(assert_render):
    assert_render("{{ value|default:True|yesno:'yes,no' }}", {}, "yes")


def test_yesno_chained_with_safe_filter(assert_render):
    assert_render("{{ value|safe|yesno:'yes,no' }}", {"value": 12}, "yes")


def test_yesno_chained_with_bool(assert_render):
    template = "{% for x in 'abc' %}{{ forloop.first|yesno }}! {% endfor %}"
    assert_render(template=template, context={}, expected="yes! no! no! ")


@pytest.mark.parametrize(
    "value,expected",
    [
        (-1.1, "yes"),
        (0.0, "no"),
        (2.2, "yes"),
    ],
)
def test_yesno_chained_with_float(assert_render, value, expected):
    template = f"{{{{ foo|default:{value}|yesno }}}}"
    assert_render(template=template, context={}, expected=expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        (-1, "yes"),
        (0, "no"),
        (2, "yes"),
    ],
)
def test_yesno_chained_with_integer(assert_render, value, expected):
    template = "{{ foo|add:0|yesno }}"
    assert_render(template=template, context={"foo": value}, expected=expected)


def test_yesno_with_empty_values(assert_render):
    assert_render("{{ value|yesno:',,' }}", {"value": True}, "")


def test_yesno_invalid_single_argument(assert_render):
    assert_render("{{ value|yesno:'yes' }}", {"value": True}, "True")


def test_yesno_with_extra_commas(assert_render):
    assert_render("{{ value|yesno:'a,b,c,d' }}", {"value": True}, "a")


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "ja"),
        (False, "nein"),
        (None, "vielleicht"),
    ],
)
def test_yesno_translation(assert_render, value, expected):
    """Test that the default 'yes,no,maybe' string is translated using gettext."""
    with override("de"):
        assert_render("{{ value|yesno }}", {"value": value}, expected)


def test_yesno_with_wrong_arg_type(assert_render_error):
    django_message = "'int' object has no attribute 'split'"
    rusty_message = """\
  × String argument expected
   ╭────
 1 │ {{ value|yesno:1000 }}
   ·                ──┬─
   ·                  ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ value|yesno:1000 }}",
        context={},
        exception=AttributeError,
        rusty_exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_yesno_with_wrong_broken_value_type(assert_render_error):
    rusty_message = """\
  × division by zero
   ╭────
 1 │ {{ broken|yesno }}
   ·           ──┬──
   ·             ╰── when calling __bool__ here
   ╰────
"""
    assert_render_error(
        template="{{ broken|yesno }}",
        context={"broken": BrokenDunderBool()},
        exception=ZeroDivisionError,
        django_message="division by zero",
        rusty_message=rusty_message,
    )


def test_yesno_invalid_html_method():
    template = engines["rusty"].from_string("{{ value|yesno:broken }}")
    context = {"broken": BrokenDunderHtml("yes,no,maybe"), "value": True}
    with pytest.raises(ZeroDivisionError) as exc_info:
        template.render(context=context)

    assert str(exc_info.value) == "division by zero"
