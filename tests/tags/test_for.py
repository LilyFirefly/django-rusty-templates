from textwrap import dedent

import pytest
from django.template import engines
from django.template.base import VariableDoesNotExist
from django.template.exceptions import TemplateSyntaxError


class BrokenIterator:
    def __len__(self):
        return 3

    def __iter__(self):
        yield 1
        yield 1 / 0


class BrokenIterator2:
    def __len__(self):
        return 3

    def __iter__(self):
        1 / 0


def test_render_for_loop(assert_render):
    template = "{% for x in y %}{{ x }}{% endfor %}"
    y = [1, 2, "foo"]
    expected = "12foo"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_reversed(assert_render):
    template = "{% for x in y reversed %}{{ x }}{% endfor %}"
    y = [1, 2, "foo"]
    expected = "foo21"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_string(assert_render):
    template = "{% for x in 'y' %}{{ x }}{% endfor %}"
    assert_render(template=template, context={}, expected="y")


def test_render_for_loop_translated_string(assert_render):
    template = "{% for x in _('y') %}{{ x }}{% endfor %}"
    assert_render(template=template, context={}, expected="y")


def test_render_for_loop_numeric():
    template = "{% for x in 1 %}{{ x }}{% endfor %}"
    django_template = engines["django"].from_string(template)

    with pytest.raises(TypeError) as exc_info:
        django_template.render()

    assert str(exc_info.value) == "'int' object is not iterable"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × 1 is not iterable
   ╭────
 1 │ {% for x in 1 %}{{ x }}{% endfor %}
   ·             ┬
   ·             ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_filter(assert_render):
    template = "{% for x in y|upper %}{{ x }}{% endfor %}"
    y = "foo"
    expected = "FOO"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_filter_reversed(assert_render):
    template = "{% for x in y|upper reversed %}{{ x }}{% endfor %}"
    y = "foo"
    expected = "OOF"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_unpack_tuple(assert_render):
    template = "{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}"
    l = [(1, 2, 3), ("foo", "bar", "spam")]
    expected = "1-2-3\nfoo-bar-spam\n"
    assert_render(template=template, context={"l": l}, expected=expected)


def test_render_for_loop_unpack_tuple_no_whitespace(assert_render):
    template = "{% for x,y in l %}{{ x }}-{{ y }}\n{% endfor %}"
    l = [(1, 2), ("foo", "bar")]
    expected = "1-2\nfoo-bar\n"
    assert_render(template=template, context={"l": l}, expected=expected)


def test_render_for_loop_unpack_dict_items(assert_render):
    template = "{% for x, y in d.items %}{{ x }}: {{ y }}\n{% endfor %}"
    d = {"foo": 1, "bar": 2}
    expected = "foo: 1\nbar: 2\n"
    assert_render(template=template, context={"d": d}, expected=expected)


def test_render_for_loop_counter(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.counter }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: 1\nbar: 2\nspam: 3\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_counter0(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.counter0 }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: 0\nbar: 1\nspam: 2\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_revcounter(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.revcounter }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: 3\nbar: 2\nspam: 1\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_revcounter0(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.revcounter0 }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: 2\nbar: 1\nspam: 0\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_first(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.first }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: True\nbar: False\nspam: False\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_last(assert_render):
    template = "{% for x in y %}{{ x }}: {{ forloop.last }}\n{% endfor %}"
    y = ["foo", "bar", "spam"]
    expected = "foo: False\nbar: False\nspam: True\n"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_forloop_variable(assert_render):
    template = "{% autoescape off %}{% for x in y %}{{ forloop }}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = "{'parentloop': {}, 'counter0': 0, 'counter': 1, 'revcounter': 1, 'revcounter0': 0, 'first': True, 'last': True}"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_forloop_variable_escaped(assert_render):
    template = "{% autoescape on %}{% for x in y %}{{ forloop }}{% endfor %}{% endautoescape on %}"
    y = ["foo"]
    expected = "{'parentloop': {}, 'counter0': 0, 'counter': 1, 'revcounter': 1, 'revcounter0': 0, 'first': True, 'last': True}".replace(
        "'", "&#x27;"
    )
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_forloop_variable_nested(assert_render):
    template = "{% autoescape off %}{% for x in y %}{% for x in y %}{{ forloop }}{% endfor %}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = "{'parentloop': {'parentloop': {}, 'counter0': 0, 'counter': 1, 'revcounter': 1, 'revcounter0': 0, 'first': True, 'last': True}, 'counter0': 0, 'counter': 1, 'revcounter': 1, 'revcounter0': 0, 'first': True, 'last': True}"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_parentloop_variable(assert_render):
    template = "{% autoescape off %}{% for x in y %}{% for x2 in y %}{{ forloop.parentloop }}{% endfor %}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = "{'parentloop': {}, 'counter0': 0, 'counter': 1, 'revcounter': 1, 'revcounter0': 0, 'first': True, 'last': True}"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_forloop_variable_no_loop(assert_render):
    template = "{% autoescape off %}{{ forloop }}{% endautoescape off %}"
    expected = "foo"
    assert_render(template=template, context={"forloop": "foo"}, expected=expected)


def test_render_for_loop_parentloop_variable_no_inner_loop(assert_render):
    template = "{% autoescape off %}{% for x in y %}{{ forloop.parentloop }}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = "{}"
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_parentloop_variable_no_inner_loop_twice(assert_render):
    template = "{% autoescape off %}{% for x in y %}{{ forloop.parentloop.parentloop }}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = ""
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_invalid_forloop_variable(assert_render):
    template = "{% autoescape off %}{% for x in y %}{{ forloop.invalid }}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = ""
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_invalid_parentloop_variable(assert_render):
    template = "{% autoescape off %}{% for x in y %}{{ forloop.invalid.parentloop }}{% endfor %}{% endautoescape off %}"
    y = ["foo"]
    expected = ""
    assert_render(template=template, context={"y": y}, expected=expected)


def test_render_for_loop_parentloop():
    template = """
    {% for x in xs %}
        {{ forloop.counter }}: {{ x }}
        {% for y in ys %}
            {{ forloop.parentloop.counter }}, {{ forloop.counter }}: {{ x }}, {{ y }}
        {% endfor %}
    {% endfor %}
    """
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    xs = ["x1", "x2", "x3"]
    ys = ["y1", "y2"]
    expected = """\
        1: x1
            1, 1: x1, y1
            1, 2: x1, y2
        2: x2
            2, 1: x2, y1
            2, 2: x2, y2
        3: x3
            3, 1: x3, y1
            3, 2: x3, y2"""

    def strip_whitespace_lines(s):
        lines = []
        for line in s.split("\n"):
            if line.strip():
                lines.append(line)
        return "\n".join(lines)

    assert (
        strip_whitespace_lines(django_template.render({"xs": xs, "ys": ys})) == expected
    )
    assert (
        strip_whitespace_lines(rust_template.render({"xs": xs, "ys": ys})) == expected
    )


def test_render_for_loop_empty(assert_render):
    template = dedent("""
    <ul>
    {% for athlete in athlete_list %}
        <li>{{ athlete.name }}</li>
    {% empty %}
        <li>sorry, no athletes in this list.</li>
    {% endfor %}
    </ul>
    """)
    expected = dedent("""
    <ul>

        <li>sorry, no athletes in this list.</li>

    </ul>
    """)
    assert_render(template=template, context={}, expected=expected)


def test_render_for_loop_shadowing_context(assert_render):
    template = "{{ x }}{% for x in y %}{{ x }}{% for x in z %}{{ x }}{% endfor %}{{ x }}{% endfor %}{{ x }}"
    context = {"x": 1, "y": [2], "z": [3]}
    expected = "12321"
    assert_render(template=template, context=context, expected=expected)


def test_render_for_loop_url_shadowing(assert_render):
    template = (
        "{{ x }}{% for x in y %}{{ x }}{% url 'home' as x %}{{ x }}{% endfor %}{{ x }}"
    )
    context = {"x": 1, "y": [2]}
    expected = "12/1"
    assert_render(template=template, context=context, expected=expected)


def test_render_in_in_in(assert_render):
    template = "{% for in in in %}{{ in }}\n{% endfor %}"
    l = (1, 2, 3)
    expected = "1\n2\n3\n"
    assert_render(template=template, context={"in": l}, expected=expected)


def test_render_number_in_expression(assert_render):
    template = "{% for 1 in l %}{{ 1 }}\n{% endfor %}"
    l = (1, 2, 3)
    expected = "1\n1\n1\n"
    assert_render(template=template, context={"l": l}, expected=expected)


def test_missing_variable_no_in():
    template = "{% for %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value) == "'for' statements should have at least four words: for"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected at least one variable name in for loop:
   ╭────
 1 │ {% for %}{% endfor %}
   · ────┬────
   ·     ╰── in this tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_variable_before_in():
    template = "{% for in %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' statements should have at least four words: for in"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a variable name before the 'in' keyword:
   ╭────
 1 │ {% for in %}{% endfor %}
   ·        ─┬
   ·         ╰── before this keyword
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_variable_before_in_four_words():
    template = "{% for in xs reversed %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' tag received an invalid argument: for in xs reversed"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a variable name before the 'in' keyword:
   ╭────
 1 │ {% for in xs reversed %}{% endfor %}
   ·        ─┬
   ·         ╰── before this keyword
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_in():
    template = "{% for x %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value) == "'for' statements should have at least four words: for x"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected the 'in' keyword or a variable name:
   ╭────
 1 │ {% for x %}{% endfor %}
   ·        ┬
   ·        ╰── after this name
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_expression_after_in():
    template = "{% for x in %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' statements should have at least four words: for x in"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected an expression after the 'in' keyword:
   ╭────
 1 │ {% for x in %}{% endfor %}
   ·          ─┬
   ·           ╰── after this keyword
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_expression_after_in_four_words():
    template = "{% for x, z in %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' statements should use the format 'for x in y': for x, z in"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected an expression after the 'in' keyword:
   ╭────
 1 │ {% for x, z in %}{% endfor %}
   ·             ─┬
   ·              ╰── after this keyword
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unpack_1_tuple():
    template = "{% for x, in l %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "'for' tag received an invalid argument: for x, in l"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected another variable when unpacking in for loop:
   ╭────
 1 │ {% for x, in l %}{% endfor %}
   ·        ┬
   ·        ╰── after this variable
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_variable_in_unpack():
    template = "{% for x, '2' in l %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value) == "'for' tag received an invalid argument: for x, '2' in l"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Invalid variable name '2' in for loop:
   ╭────
 1 │ {% for x, '2' in l %}{% endfor %}
   ·           ─┬─
   ·            ╰── invalid variable name
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_expression_before_in():
    template = "{% for x y in l %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "'for' tag received an invalid argument: for x y in l"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected expression in for loop. Did you miss a comma when unpacking?
   ╭────
 1 │ {% for x y in l %}{% endfor %}
   ·          ┬
   ·          ╰── unexpected expression
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_expression_before_in_longer():
    template = "{% for x, y, z w in l %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' tag received an invalid argument: for x, y, z w in l"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected expression in for loop. Did you miss a comma when unpacking?
   ╭────
 1 │ {% for x, y, z w in l %}{% endfor %}
   ·                ┬
   ·                ╰── unexpected expression
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_expression_after_in():
    template = "{% for x in l m %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' statements should use the format 'for x in y': for x in l m"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected expression in for loop:
   ╭────
 1 │ {% for x in l m %}{% endfor %}
   ·               ┬
   ·               ╰── unexpected expression
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_expression_after_reversed():
    template = "{% for x in l reversed m %}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "'for' statements should use the format 'for x in y': for x in l reversed m"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected expression in for loop:
   ╭────
 1 │ {% for x in l reversed m %}{% endfor %}
   ·                        ┬
   ·                        ╰── unexpected expression
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_unpack_tuple_mismatch():
    template = "{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    l = [(1, 2, 3), ("foo", "bar")]

    with pytest.raises(ValueError) as exc_info:
        django_template.render({"l": l})

    assert str(exc_info.value) == "Need 3 values to unpack in for loop; got 2. "

    with pytest.raises(ValueError) as exc_info:
        rust_template.render({"l": l})

    expected = """\
  × Need 3 values to unpack; got 2.
   ╭─[1:8]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·        ───┬───    ┬
   ·           │       ╰── from here
   ·           ╰── unpacked here
 2 │ {% endfor %}
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_unpack_tuple_invalid():
    template = "{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    l = [1]

    with pytest.raises(ValueError) as exc_info:
        django_template.render({"l": l})

    assert str(exc_info.value) == "Need 3 values to unpack in for loop; got 1. "

    with pytest.raises(ValueError) as exc_info:
        rust_template.render({"l": l})

    expected = """\
  × Need 3 values to unpack; got 1.
   ╭─[1:8]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·        ───┬───    ┬
   ·           │       ╰── from here
   ·           ╰── unpacked here
 2 │ {% endfor %}
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_unpack_tuple_iteration_error():
    template = "{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    l = [BrokenIterator()]

    with pytest.raises(ZeroDivisionError) as exc_info:
        django_template.render({"l": l})

    assert str(exc_info.value) == "division by zero"

    with pytest.raises(ZeroDivisionError) as exc_info:
        rust_template.render({"l": l})

    expected = """\
  × division by zero
   ╭─[1:19]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·                   ┬
   ·                   ╰── while unpacking this
 2 │ {% endfor %}
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_unpack_tuple_broken_iterator():
    template = "{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    l = [BrokenIterator2()]

    with pytest.raises(ZeroDivisionError) as exc_info:
        django_template.render({"l": l})

    assert str(exc_info.value) == "division by zero"

    with pytest.raises(ZeroDivisionError) as exc_info:
        rust_template.render({"l": l})

    expected = """\
  × division by zero
   ╭─[1:19]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·                   ┬
   ·                   ╰── while iterating this
 2 │ {% endfor %}
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_unpack_string():
    template = "{% for x, y in 'foo' %}{{ x }}{{ y }}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    l = [(1, 2, 3), ("foo", "bar")]

    with pytest.raises(ValueError) as exc_info:
        django_template.render({"l": l})

    assert str(exc_info.value) == "Need 2 values to unpack in for loop; got 1. "

    with pytest.raises(ValueError) as exc_info:
        rust_template.render({"l": l})

    expected = """\
  × Need 2 values to unpack; got 1.
   ╭────
 1 │ {% for x, y in 'foo' %}{{ x }}{{ y }}{% endfor %}
   ·        ──┬─    ──┬──
   ·          │       ╰── from here
   ·          ╰── unpacked here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_invalid_variable():
    template = "{% for x in _a %}{{ x }}{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Variables and attributes may not begin with underscores: '_a'"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% for x in _a %}{{ x }}{% endfor %}
   ·             ─┬
   ·              ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_empty_tag():
    template = "{% empty %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 1: 'empty'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag empty
   ╭────
 1 │ {% empty %}
   · ─────┬─────
   ·      ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_endfor_tag():
    template = "{% endfor %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 1: 'endfor'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag endfor
   ╭────
 1 │ {% endfor %}
   · ──────┬─────
   ·       ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_missing_endfor_tag():
    template = "{% for x in 'a' %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Unclosed tag on line 1: 'for'. Looking for one of: empty, endfor."
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unclosed 'for' tag. Looking for one of: empty, endfor
   ╭────
 1 │ {% for x in 'a' %}
   · ─────────┬────────
   ·          ╰── started here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_missing_endfor_tag_after_empty():
    template = "{% for x in 'a' %}{% empty %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Unclosed tag on line 1: 'for'. Looking for one of: endfor."
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unclosed 'empty' tag. Looking for one of: endfor
   ╭────
 1 │ {% for x in 'a' %}{% empty %}
   ·                   ─────┬─────
   ·                        ╰── started here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_not_iterable():
    template = "{% for x in a %}{{ x }}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(TypeError) as exc_info:
        django_template.render({"a": 1})

    assert str(exc_info.value) == "'int' object is not iterable"

    with pytest.raises(TypeError) as exc_info:
        rust_template.render({"a": 1})

    expected = """\
  × 'int' object is not iterable
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}
   ·             ┬
   ·             ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_iteration_error():
    template = "{% for x in a %}{{ x }}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(ZeroDivisionError) as exc_info:
        django_template.render({"a": BrokenIterator()})

    assert str(exc_info.value) == "division by zero"

    with pytest.raises(ZeroDivisionError) as exc_info:
        rust_template.render({"a": BrokenIterator()})

    expected = """\
  × division by zero
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}
   ·             ┬
   ·             ╰── while iterating this
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_body_error():
    template = "{% for x in a %}{% for y in 'b' %}{{ x|add:z }}{% endfor %}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(VariableDoesNotExist) as exc_info:
        django_template.render({"a": [1]})

    error = "Failed lookup for key [z] in [{'True': True, 'False': False, 'None': None}, {'a': [1]}]"
    assert str(exc_info.value) == error

    with pytest.raises(VariableDoesNotExist) as exc_info:
        rust_template.render({"a": [1]})

    expected = """\
  × Failed lookup for key [z] in {"False": False, "None": None, "True": True,
  │ "a": [1], "x": 1, "y": 'b'}
   ╭────
 1 │ {% for x in a %}{% for y in 'b' %}{{ x|add:z }}{% endfor %}{% endfor %}
   ·                                            ┬
   ·                                            ╰── key
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_for_loop_missing():
    template = "{% for x in a|default:b %}{{ x }}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(VariableDoesNotExist) as exc_info:
        django_template.render({})

    error = "Failed lookup for key [b] in [{'True': True, 'False': False, 'None': None}, {}]"
    assert str(exc_info.value) == error

    with pytest.raises(VariableDoesNotExist) as exc_info:
        rust_template.render({})

    expected = """\
  × Failed lookup for key [b] in {"False": False, "None": None, "True": True}
   ╭────
 1 │ {% for x in a|default:b %}{{ x }}{% endfor %}
   ·                       ┬
   ·                       ╰── key
   ╰────
"""
    assert str(exc_info.value) == expected


def test_missing_argument_after_for_loop():
    template = "{% for x in a %}{{ x }}{% endfor %}{{ y|default:x }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(VariableDoesNotExist) as exc_info:
        django_template.render({"a": "b"})

    error = "Failed lookup for key [x] in [{'True': True, 'False': False, 'None': None}, {'a': 'b'}]"
    assert str(exc_info.value) == error

    with pytest.raises(VariableDoesNotExist) as exc_info:
        rust_template.render({"a": "b"})

    expected = """\
  × Failed lookup for key [x] in {"False": False, "None": None, "True": True,
  │ "a": 'b'}
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}{{ y|default:x }}
   ·                                                 ┬
   ·                                                 ╰── key
   ╰────
"""
    assert str(exc_info.value) == expected
