import pytest


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


def test_yesno_with_empty_values(assert_render):
    assert_render("{{ value|yesno:',,' }}", {"value": True}, "")


def test_yesno_invalid_single_argument(assert_render):
    assert_render("{{ value|yesno:'yes' }}", {"value": True}, "True")


def test_yesno_with_extra_commas(assert_render):
    assert_render("{{ value|yesno:'a,b,c,d' }}", {"value": True}, "a")
