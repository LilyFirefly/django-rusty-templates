import pytest
from inline_snapshot import snapshot

from django.template import VariableDoesNotExist


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ value|divisibleby:2 }}",
            {"value": 4},
            "True",
            id="divisibleby_even_true",
        ),
        pytest.param(
            "{{ value|divisibleby:2 }}",
            {"value": 5},
            "False",
            id="divisibleby_even_false",
        ),
        pytest.param(
            "{{ value|divisibleby:5 }}",
            {"value": 0},
            "True",
            id="divisibleby_zero",
        ),
        pytest.param(
            "{{ value|divisibleby:3 }}",
            {"value": 9},
            "True",
            id="divisibleby_exact",
        ),
        pytest.param(
            "{{ value|divisibleby:3 }}",
            {"value": 10},
            "False",
            id="divisibleby_not_exact",
        ),
    ],
)
def test_divisibleby(assert_render, template, context, expected):
    assert_render(template, context, expected)


@pytest.mark.parametrize(
    "value,arg,expected",
    [
        (-10, 5, "True"),
        (-10, 3, "False"),
        (10, -5, "True"),
        (-9, -3, "True"),
    ],
)
def test_divisibleby_negative_numbers(assert_render, value, arg, expected):
    template = f"{{{{ {value}|divisibleby:{arg} }}}}"
    assert_render(template, {}, expected)


def test_divisibleby_string_number(assert_render):
    template = "{{ value|divisibleby:2 }}"
    context = {"value": "6"}
    expected = "True"
    assert_render(template, context, expected)


def test_divisibleby_large_numbers(assert_render):
    large_num = 10**50
    template = f"{{{{ {large_num}|divisibleby:10 }}}}"
    assert_render(template, {}, "True")


def test_divisibleby_missing_variable(assert_render_error):
    template = "{{ missing|divisibleby:2 }}"
    context = {}
    assert_render_error(
        template=template,
        context=context,
        exception=ValueError,
        django_message=snapshot("invalid literal for int() with base 10: ''"),
        rusty_message=snapshot("""\
  × invalid literal for int() with base 10: ''
   ╭────
 1 │ {{ missing|divisibleby:2 }}
   ·            ─────┬─────
   ·                 ╰── here
   ╰────
"""),
    )


def test_divisibleby_none(assert_render_error):
    template = "{{ value|divisibleby:2 }}"
    context = {"value": None}
    assert_render_error(
        template=template,
        context=context,
        exception=TypeError,
        django_message=snapshot(
            "int() argument must be a string, a bytes-like object or a real number, not 'NoneType'"
        ),
        rusty_message=snapshot("""\
  × int() argument must be a string, a bytes-like object or a real number, not
  │ 'NoneType'
   ╭────
 1 │ {{ value|divisibleby:2 }}
   ·          ─────┬─────
   ·               ╰── here
   ╰────
"""),
    )


def test_divisibleby_zero_division(assert_render_error):
    template = "{{ 10|divisibleby:0 }}"
    context = {}
    assert_render_error(
        template=template,
        context=context,
        exception=ZeroDivisionError,
        django_message=snapshot("integer modulo by zero"),
        rusty_message=snapshot("""\
  × integer modulo by zero
   ╭────
 1 │ {{ 10|divisibleby:0 }}
   ·                   ┬
   ·                   ╰── here
   ╰────
"""),
    )


def test_divisibleby_no_argument(assert_parse_error):
    django_message = snapshot("divisibleby requires 2 arguments, 1 provided")
    rusty_message = snapshot("""\
  × Expected an argument
   ╭────
 1 │ {{ value|divisibleby }}
   ·          ─────┬─────
   ·               ╰── here
   ╰────
""")
    assert_parse_error(
        template="{{ value|divisibleby }}",
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_divisibleby_error_missing_arg_variable(assert_render_error):
    template = "{{ value|divisibleby:arg }}"
    context = {"value": 10}

    assert_render_error(
        template=template,
        context=context,
        exception=VariableDoesNotExist,
        django_message=snapshot(
            "Failed lookup for key [arg] in [{'True': True, 'False': False, 'None': None}, {'value': 10}]"
        ),
        rusty_message=snapshot("""\
  × Failed lookup for key [arg] in {"False": False, "None": None, "True":
  │ True, "value": 10}
   ╭────
 1 │ {{ value|divisibleby:arg }}
   ·                      ─┬─
   ·                       ╰── key
   ╰────
"""),
    )


def test_divisibleby_error_invalid_arg_type(assert_render_error):
    template = "{{ value|divisibleby:bad_arg }}"
    context = {"value": 10, "bad_arg": [1, 2]}

    assert_render_error(
        template=template,
        context=context,
        exception=TypeError,
        rusty_exception=TypeError,
        django_message=snapshot(
            "int() argument must be a string, a bytes-like object or a real number, not 'list'"
        ),
        rusty_message=snapshot("""\
  × Integer argument expected
   ╭────
 1 │ {{ value|divisibleby:bad_arg }}
   ·                      ───┬───
   ·                         ╰── here
   ╰────
"""),
    )


def test_divisibleby_right_zero_negative(assert_render_error):
    template = "{{ 10|divisibleby:-0 }}"
    context = {}
    assert_render_error(
        template=template,
        context=context,
        exception=ZeroDivisionError,
        django_message="integer modulo by zero",
        rusty_message="""\
  × integer modulo by zero
   ╭────
 1 │ {{ 10|divisibleby:-0 }}
   ·                   ─┬
   ·                    ╰── here
   ╰────
""",
    )


def test_divisibleby_arg_variable(assert_render):
    template = "{{ value|divisibleby:arg }}"
    context = {"value": 10, "arg": 5}
    expected = "True"
    assert_render(template, context, expected)


def test_divisibleby_arg_string_number(assert_render):
    template = "{{ value|divisibleby:arg }}"
    context = {"value": 10, "arg": "5"}
    expected = "True"
    assert_render(template, context, expected)


def test_divisibleby_right_argument_via_add(assert_render):
    template = "{{ value|divisibleby:arg|add:0 }}"
    context = {"value": 10, "arg": 5}
    expected = "1"
    assert_render(template, context, expected)
