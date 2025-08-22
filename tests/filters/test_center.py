import pytest
from django.template import engines
from django.template.exceptions import TemplateSyntaxError


def test_center(assert_render):
    template = "{{ var|center:5 }}"
    context = {"var": "123"}
    expected = " 123 "

    assert_render(template, context, expected)


def test_center_with_odd_width_as_django_test_it(assert_render):
    template = "{{ var|center:15 }}"
    context = {"var": "Django"}
    expected = "     Django    "

    assert_render(template, context, expected)


def test_center_with_even_width(assert_render):
    template = "{{ var|center:6 }}"
    context = {"var": "odd"}
    expected = " odd  "

    assert_render(template, context, expected)


def test_center_with_odd_width(assert_render):
    template = "{{ var|center:7 }}"
    context = {"var": "even"}
    expected = "  even "

    assert_render(template, context, expected)


def test_add_no_argument():
    template = "{{ foo|center }}"
    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "center requires 2 arguments, 1 provided"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected an argument
   ╭────
 1 │ {{ foo|center }}
   ·        ───┬──
   ·           ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_argument_not_integer():
    template = "{{ foo|center:bar }}"
    expected = "invalid literal for int() with base 10: 'not an integer'"
    with pytest.raises(ValueError) as exc_info:
        engines["django"].from_string(template).render(
            {"foo": "test", "bar": "not an integer"}
        )

    assert str(exc_info.value) == expected

    with pytest.raises(ValueError) as exc_info:
        engines["rusty"].from_string(template).render(
            {"foo": "test", "bar": "not an integer"}
        )

    expected = """\
  × Couldn't convert argument (not an integer) to integer
   ╭────
 1 │ {{ foo|center:bar }}
   ·               ─┬─
   ·                ╰── argument
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_less_than_string_length(assert_render):
    template = "{{ foo|center:2 }}"
    context = {"foo": "test"}
    expected = "test"  # No padding since the width is less than the string length

    assert_render(template, context, expected)


def test_center_argument_float(assert_render):
    template = "{{ foo|center:6.5 }}"
    context = {"foo": "test"}
    expected = " test "

    assert_render(template, context, expected)


def test_center_argument_negative_integer(assert_render):
    template = "{{ foo|center:-5 }}"
    context = {"foo": "test"}
    expected = "test"  # No padding since the width is negative

    assert_render(template, context, expected)


def test_center_argument_negative_float(assert_render):
    template = "{{ foo|center:-5.5 }}"
    context = {"foo": "test"}
    expected = "test"  # No padding since the width is negative

    assert_render(template, context, expected)


def test_center_argument_is_negative_integer_as_string(assert_render):
    template = "{{ foo|center:'-5' }}"
    context = {"foo": "test"}
    expected = "test"  # No padding since the width is negative

    assert_render(template, context, expected)


@pytest.mark.parametrize("foo,expected", [("", " "), ("foo", "foofoo")])
def test_center_by_bool(assert_render, foo, expected):
    template = "{% for x in 'xy' %}{{ foo|center:forloop.first }}{% endfor %}"
    context = {"foo": foo}

    assert_render(template, context, expected)


def test_center_argument_is_negative_float_as_string():
    template = "{{ foo|center:bar }}"

    with pytest.raises(ValueError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test", "bar": "-5.5"})

    assert str(exc_info.value) == "invalid literal for int() with base 10: '-5.5'"

    with pytest.raises(ValueError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test", "bar": "-5.5"})

    expected = """\
  × Couldn't convert argument (-5.5) to integer
   ╭────
 1 │ {{ foo|center:bar }}
   ·               ─┬─
   ·                ╰── argument
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_bigger_than_isize_max():
    template = "{{ foo|center:9223372036854775808 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:9223372036854775808 }}
   ·               ─────────┬─────────
   ·                        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_smaller_than_isize_min():
    template = "{{ foo|center:-9223372036854775809 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:-9223372036854775809 }}
   ·               ──────────┬─────────
   ·                         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_bigger_than_isize_max_string():
    template = "{{ foo|center:'9223372036854775808' }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:'9223372036854775808' }}
   ·               ──────────┬──────────
   ·                         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_smaller_than_isize_min_string():
    template = "{{ foo|center:'-9223372036854775809' }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:'-9223372036854775809' }}
   ·               ───────────┬──────────
   ·                          ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_bigger_than_isize_max_python():
    template = "{{ foo|center:width }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test", "width": 9223372036854775808})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test", "width": 9223372036854775808})

    expected = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_int_smaller_than_isize_min_python():
    template = "{{ foo|center:width }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test", "width": -9223372036854775809})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test", "width": -9223372036854775809})

    expected = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_string():
    template = "{{ foo|center:'foo' }}"

    with pytest.raises(ValueError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "invalid literal for int() with base 10: 'foo'"

    with pytest.raises(ValueError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Couldn't convert argument ('foo') to integer
   ╭────
 1 │ {{ foo|center:'foo' }}
   ·               ──┬──
   ·                 ╰── argument
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_bigger_than_isize_max():
    template = "{{ foo|center:9223372036854775808.0 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:9223372036854775808.0 }}
   ·               ──────────┬──────────
   ·                         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_smaller_than_isize_min():
    # Note this float literal is equivalent to -9223372036854777856.0
    # because of limitations of float accuracy
    template = "{{ foo|center:-9223372036854776833.0 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "Python int too large to convert to C ssize_t"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Integer -9223372036854777856 is too large
   ╭────
 1 │ {{ foo|center:-9223372036854776833.0 }}
   ·               ───────────┬──────────
   ·                          ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_inf():
    template = "{{ foo|center:1e310 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "cannot convert float infinity to integer"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ foo|center:1e310 }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_negative_inf():
    template = "{{ foo|center:-1e310 }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test"})

    assert str(exc_info.value) == "cannot convert float infinity to integer"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test"})

    expected = """\
  × Couldn't convert float (-inf) to integer
   ╭────
 1 │ {{ foo|center:-1e310 }}
   ·               ───┬──
   ·                  ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_inf_python():
    template = "{{ foo|center:width }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test", "width": float("inf")})

    assert str(exc_info.value) == "cannot convert float infinity to integer"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test", "width": float("inf")})

    expected = """\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_center_argument_float_negative_inf_python():
    template = "{{ foo|center:width }}"

    with pytest.raises(OverflowError) as exc_info:
        engines["django"].from_string(template).render({"foo": "test", "width": float("-inf")})

    assert str(exc_info.value) == "cannot convert float infinity to integer"

    with pytest.raises(OverflowError) as exc_info:
        engines["rusty"].from_string(template).render({"foo": "test", "width": float("-inf")})

    expected = """\
  × Couldn't convert float (-inf) to integer
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected
