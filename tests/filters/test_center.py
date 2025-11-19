import pytest


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


def test_add_no_argument(assert_parse_error):
    template = "{{ foo|center }}"
    django_message = "center requires 2 arguments, 1 provided"
    rusty_message = """\
  × Expected an argument
   ╭────
 1 │ {{ foo|center }}
   ·        ───┬──
   ·           ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_argument_not_integer(assert_render_error):
    django_message = "invalid literal for int() with base 10: 'not an integer'"
    rusty_message = """\
  × Couldn't convert argument (not an integer) to integer
   ╭────
 1 │ {{ foo|center:bar }}
   ·               ─┬─
   ·                ╰── argument
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:bar }}",
        context={"foo": "test", "bar": "not an integer"},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


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


@pytest.mark.parametrize("value", [True, False])
def test_center_argument_bool(assert_render, value):
    """Behaves like 1 and 0"""
    template = f"{{{{ foo|center:{value} }}}}"
    context = {"foo": "test"}
    expected = "test"

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


def test_center_argument_is_negative_float_as_string(assert_render_error):
    django_message = "invalid literal for int() with base 10: '-5.5'"
    rusty_message = """\
  × Couldn't convert argument (-5.5) to integer
   ╭────
 1 │ {{ foo|center:bar }}
   ·               ─┬─
   ·                ╰── argument
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:bar }}",
        context={"foo": "test", "bar": "-5.5"},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_bigger_than_isize_max(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:9223372036854775808 }}
   ·               ─────────┬─────────
   ·                        ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:9223372036854775808 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_smaller_than_isize_min(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:-9223372036854775809 }}
   ·               ──────────┬─────────
   ·                         ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:-9223372036854775809 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_bigger_than_isize_max_string(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:'9223372036854775808' }}
   ·               ──────────┬──────────
   ·                         ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:'9223372036854775808' }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_smaller_than_isize_min_string(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:'-9223372036854775809' }}
   ·               ───────────┬──────────
   ·                          ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:'-9223372036854775809' }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_bigger_than_isize_max_python(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:width }}",
        context={"foo": "test", "width": 9223372036854775808},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_int_smaller_than_isize_min_python(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer -9223372036854775809 is too large
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:width }}",
        context={"foo": "test", "width": -9223372036854775809},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_string(assert_render_error):
    django_message = "invalid literal for int() with base 10: 'foo'"
    rusty_message = """\
  × Couldn't convert argument ('foo') to integer
   ╭────
 1 │ {{ foo|center:'foo' }}
   ·               ──┬──
   ·                 ╰── argument
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:'foo' }}",
        context={"foo": "test"},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_bigger_than_isize_max(assert_render_error):
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer 9223372036854775808 is too large
   ╭────
 1 │ {{ foo|center:9223372036854775808.0 }}
   ·               ──────────┬──────────
   ·                         ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:9223372036854775808.0 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_smaller_than_isize_min(assert_render_error):
    # Note this float literal is equivalent to -9223372036854777856.0
    # because of limitations of float accuracy
    django_message = "Python int too large to convert to C ssize_t"
    rusty_message = """\
  × Integer -9223372036854777856 is too large
   ╭────
 1 │ {{ foo|center:-9223372036854776833.0 }}
   ·               ───────────┬──────────
   ·                          ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:-9223372036854776833.0 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_inf(assert_render_error):
    django_message = "cannot convert float infinity to integer"
    rusty_message = """\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ foo|center:1e310 }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:1e310 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_negative_inf(assert_render_error):
    django_message = "cannot convert float infinity to integer"
    rusty_message = """\
  × Couldn't convert float (-inf) to integer
   ╭────
 1 │ {{ foo|center:-1e310 }}
   ·               ───┬──
   ·                  ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:-1e310 }}",
        context={"foo": "test"},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_inf_python(assert_render_error):
    django_message = "cannot convert float infinity to integer"
    rusty_message = """\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:width }}",
        context={"foo": "test", "width": float("inf")},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_center_argument_float_negative_inf_python(assert_render_error):
    django_message = "cannot convert float infinity to integer"
    rusty_message = """\
  × Couldn't convert float (-inf) to integer
   ╭────
 1 │ {{ foo|center:width }}
   ·               ──┬──
   ·                 ╰── here
   ╰────
"""
    assert_render_error(
        template="{{ foo|center:width }}",
        context={"foo": "test", "width": float("-inf")},
        exception=OverflowError,
        django_message=django_message,
        rusty_message=rusty_message,
    )
