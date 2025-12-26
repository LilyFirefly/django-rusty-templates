from inline_snapshot import snapshot
import pytest


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(None, "default_value", id="none_value"),
        pytest.param("", "default_value", id="empty_string"),
        pytest.param(0, "default_value", id="zero"),
        pytest.param(False, "default_value", id="false"),
        pytest.param("actual_value", "actual_value", id="string_value"),
        pytest.param(42, "42", id="integer_value"),
        pytest.param(3.14, "3.14", id="float_value"),
        pytest.param(True, "True", id="true_value"),
        pytest.param([], "default_value", id="empty_list"),
        pytest.param({}, "default_value", id="empty_dict"),
    ],
)
def test_default_with_various_values(assert_render, value, expected):
    template = "{{ value|default:'default_value' }}"
    assert_render(template=template, context={"value": value}, expected=expected)


def test_default_with_missing_variable(assert_render):
    template = "{{ missing|default:'default' }}"
    assert_render(template=template, context={}, expected="default")


class Broken:
    def __bool__(self):
        1 / 0


def test_default_broken_bool(assert_render_error):
    django_message = snapshot("division by zero")
    rusty_message = snapshot("""\
  × division by zero
   ╭────
 1 │ {{ value|default:'default' }}
   ·          ───┬───
   ·             ╰── here
   ╰────
""")
    assert_render_error(
        template="{{ value|default:'default' }}",
        context={"value": Broken()},
        exception=ZeroDivisionError,
        django_message=django_message,
        rusty_message=rusty_message,
    )
