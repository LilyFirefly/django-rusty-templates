from inline_snapshot import snapshot
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


def test_render_for_loop_parentloop(template_engine):
    template = """
    {% for x in xs %}
        {{ forloop.counter }}: {{ x }}
        {% for y in ys %}
            {{ forloop.parentloop.counter }}, {{ forloop.counter }}: {{ x }}, {{ y }}
        {% endfor %}
    {% endfor %}
    """
    template_obj = template_engine.from_string(template)

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

    assert strip_whitespace_lines(template_obj.render({"xs": xs, "ys": ys})) == expected


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


def test_missing_variable_no_in(assert_parse_error):
    template = "{% for %}{% endfor %}"
    django_message = snapshot("'for' statements should have at least four words: for")
    rusty_message = snapshot("""\
  × Expected at least one variable name in for loop:
   ╭────
 1 │ {% for %}{% endfor %}
   · ────┬────
   ·     ╰── in this tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_variable_before_in(assert_parse_error):
    template = "{% for in %}{% endfor %}"
    django_message = snapshot(
        "'for' statements should have at least four words: for in"
    )
    rusty_message = snapshot("""\
  × Expected a variable name before the 'in' keyword:
   ╭────
 1 │ {% for in %}{% endfor %}
   ·        ─┬
   ·         ╰── before this keyword
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_variable_before_in_four_words(assert_parse_error):
    template = "{% for in xs reversed %}{% endfor %}"
    django_message = snapshot(
        "'for' tag received an invalid argument: for in xs reversed"
    )
    rusty_message = snapshot("""\
  × Expected a variable name before the 'in' keyword:
   ╭────
 1 │ {% for in xs reversed %}{% endfor %}
   ·        ─┬
   ·         ╰── before this keyword
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_in(assert_parse_error):
    template = "{% for x %}{% endfor %}"
    django_message = snapshot("'for' statements should have at least four words: for x")
    rusty_message = snapshot("""\
  × Expected the 'in' keyword or a variable name:
   ╭────
 1 │ {% for x %}{% endfor %}
   ·        ┬
   ·        ╰── after this name
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_expression_after_in(assert_parse_error):
    template = "{% for x in %}{% endfor %}"
    django_message = snapshot(
        "'for' statements should have at least four words: for x in"
    )
    rusty_message = snapshot("""\
  × Expected an expression after the 'in' keyword:
   ╭────
 1 │ {% for x in %}{% endfor %}
   ·          ─┬
   ·           ╰── after this keyword
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_expression_after_in_four_words(assert_parse_error):
    template = "{% for x, z in %}{% endfor %}"
    django_message = snapshot(
        "'for' statements should use the format 'for x in y': for x, z in"
    )
    rusty_message = snapshot("""\
  × Expected an expression after the 'in' keyword:
   ╭────
 1 │ {% for x, z in %}{% endfor %}
   ·             ─┬
   ·              ╰── after this keyword
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unpack_1_tuple(assert_parse_error):
    template = "{% for x, in l %}{% endfor %}"
    django_message = snapshot("'for' tag received an invalid argument: for x, in l")
    rusty_message = snapshot("""\
  × Expected another variable when unpacking in for loop:
   ╭────
 1 │ {% for x, in l %}{% endfor %}
   ·        ┬
   ·        ╰── after this variable
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_variable_in_unpack(assert_parse_error):
    template = "{% for x, '2' in l %}{% endfor %}"
    django_message = snapshot("'for' tag received an invalid argument: for x, '2' in l")
    rusty_message = snapshot("""\
  × Invalid variable name '2' in for loop:
   ╭────
 1 │ {% for x, '2' in l %}{% endfor %}
   ·           ─┬─
   ·            ╰── invalid variable name
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unexpected_expression_before_in(assert_parse_error):
    template = "{% for x y in l %}{% endfor %}"
    django_message = snapshot("'for' tag received an invalid argument: for x y in l")
    rusty_message = snapshot("""\
  × Unexpected expression in for loop. Did you miss a comma when unpacking?
   ╭────
 1 │ {% for x y in l %}{% endfor %}
   ·          ┬
   ·          ╰── unexpected expression
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unexpected_expression_before_in_longer(assert_parse_error):
    template = "{% for x, y, z w in l %}{% endfor %}"
    django_message = snapshot(
        "'for' tag received an invalid argument: for x, y, z w in l"
    )
    rusty_message = snapshot("""\
  × Unexpected expression in for loop. Did you miss a comma when unpacking?
   ╭────
 1 │ {% for x, y, z w in l %}{% endfor %}
   ·                ┬
   ·                ╰── unexpected expression
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unexpected_expression_after_in(assert_parse_error):
    template = "{% for x in l m %}{% endfor %}"
    django_message = snapshot(
        "'for' statements should use the format 'for x in y': for x in l m"
    )
    rusty_message = snapshot("""\
  × Unexpected expression in for loop:
   ╭────
 1 │ {% for x in l m %}{% endfor %}
   ·               ┬
   ·               ╰── unexpected expression
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unexpected_expression_after_reversed(assert_parse_error):
    template = "{% for x in l reversed m %}{% endfor %}"
    django_message = (
        "'for' statements should use the format 'for x in y': for x in l reversed m"
    )
    rusty_message = snapshot("""\
  × Unexpected expression in for loop:
   ╭────
 1 │ {% for x in l reversed m %}{% endfor %}
   ·                        ┬
   ·                        ╰── unexpected expression
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_for_loop_unpack_tuple_mismatch(assert_render_error):
    django_message = snapshot("Need 3 values to unpack in for loop; got 2. ")
    rusty_message = snapshot("""\
  × Need 3 values to unpack; got 2.
   ╭─[1:8]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·        ───┬───    ┬
   ·           │       ╰── from here
   ·           ╰── unpacked here
 2 │ {% endfor %}
   ╰────
""")
    assert_render_error(
        template="{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}",
        context={"l": [(1, 2, 3), ("foo", "bar")]},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_unpack_tuple_invalid(assert_render_error):
    django_message = snapshot("Need 3 values to unpack in for loop; got 1. ")
    rusty_message = snapshot("""\
  × Need 3 values to unpack; got 1.
   ╭─[1:8]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·        ───┬───    ┬
   ·           │       ╰── from here
   ·           ╰── unpacked here
 2 │ {% endfor %}
   ╰────
""")
    assert_render_error(
        template="{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}",
        context={"l": [1]},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_unpack_tuple_iteration_error(assert_render_error):
    django_message = snapshot("division by zero")
    rusty_message = snapshot("""\
  × division by zero
   ╭─[1:19]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·                   ┬
   ·                   ╰── while unpacking this
 2 │ {% endfor %}
   ╰────
""")
    assert_render_error(
        template="{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}",
        context={"l": [BrokenIterator()]},
        exception=ZeroDivisionError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_unpack_tuple_broken_iterator(assert_render_error):
    django_message = snapshot("division by zero")
    rusty_message = snapshot("""\
  × division by zero
   ╭─[1:19]
 1 │ {% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}
   ·                   ┬
   ·                   ╰── while iterating this
 2 │ {% endfor %}
   ╰────
""")
    assert_render_error(
        template="{% for x, y, z in l %}{{ x }}-{{ y }}-{{ z }}\n{% endfor %}",
        context={"l": [BrokenIterator2()]},
        exception=ZeroDivisionError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_unpack_string(assert_render_error):
    django_message = snapshot("Need 2 values to unpack in for loop; got 1. ")
    rusty_message = snapshot("""\
  × Need 2 values to unpack; got 1.
   ╭────
 1 │ {% for x, y in 'foo' %}{{ x }}{{ y }}{% endfor %}
   ·        ──┬─    ──┬──
   ·          │       ╰── from here
   ·          ╰── unpacked here
   ╰────
""")
    assert_render_error(
        template="{% for x, y in 'foo' %}{{ x }}{{ y }}{% endfor %}",
        context={"l": [(1, 2, 3), ("foo", "bar")]},
        exception=ValueError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_invalid_variable(assert_parse_error):
    template = "{% for x in _a %}{{ x }}{% endfor %}"
    django_message = snapshot(
        "Variables and attributes may not begin with underscores: '_a'"
    )
    rusty_message = snapshot("""\
  × Expected a valid variable name
   ╭────
 1 │ {% for x in _a %}{{ x }}{% endfor %}
   ·             ─┬
   ·              ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_empty_tag(assert_parse_error):
    template = "{% empty %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'empty'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag empty
   ╭────
 1 │ {% empty %}
   · ─────┬─────
   ·      ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_endfor_tag(assert_parse_error):
    template = "{% endfor %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endfor'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag endfor
   ╭────
 1 │ {% endfor %}
   · ──────┬─────
   ·       ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_missing_endfor_tag(assert_parse_error):
    template = "{% for x in 'a' %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'for'. Looking for one of: empty, endfor."
    )
    rusty_message = snapshot("""\
  × Unclosed 'for' tag. Looking for one of: empty, endfor
   ╭────
 1 │ {% for x in 'a' %}
   · ─────────┬────────
   ·          ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_missing_endfor_tag_after_empty(assert_parse_error):
    template = "{% for x in 'a' %}{% empty %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'for'. Looking for one of: endfor."
    )
    rusty_message = snapshot("""\
  × Unclosed 'empty' tag. Looking for one of: endfor
   ╭────
 1 │ {% for x in 'a' %}{% empty %}
   ·                   ─────┬─────
   ·                        ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_for_loop_not_iterable(assert_render_error):
    django_message = snapshot("'int' object is not iterable")
    rusty_message = snapshot("""\
  × 'int' object is not iterable
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}
   ·             ┬
   ·             ╰── here
   ╰────
""")
    assert_render_error(
        template="{% for x in a %}{{ x }}{% endfor %}",
        context={"a": 1},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_iteration_error(assert_render_error):
    django_message = snapshot("division by zero")
    rusty_message = snapshot("""\
  × division by zero
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}
   ·             ┬
   ·             ╰── while iterating this
   ╰────
""")
    assert_render_error(
        template="{% for x in a %}{{ x }}{% endfor %}",
        context={"a": BrokenIterator()},
        exception=ZeroDivisionError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_body_error(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [z] in [{'True': True, 'False': False, 'None': None}, {'a': [1]}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [z] in {"False": False, "None": None, "True": True,
  │ "a": [1], "x": 1, "y": 'b'}
   ╭────
 1 │ {% for x in a %}{% for y in 'b' %}{{ x|add:z }}{% endfor %}{% endfor %}
   ·                                            ┬
   ·                                            ╰── key
   ╰────
""")
    assert_render_error(
        template="{% for x in a %}{% for y in 'b' %}{{ x|add:z }}{% endfor %}{% endfor %}",
        context={"a": [1]},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_for_loop_missing(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [b] in [{'True': True, 'False': False, 'None': None}, {}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [b] in {"False": False, "None": None, "True": True}
   ╭────
 1 │ {% for x in a|default:b %}{{ x }}{% endfor %}
   ·                       ┬
   ·                       ╰── key
   ╰────
""")
    assert_render_error(
        template="{% for x in a|default:b %}{{ x }}{% endfor %}",
        context={},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_missing_argument_after_for_loop(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [x] in [{'True': True, 'False': False, 'None': None}, {'a': 'b'}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [x] in {"False": False, "None": None, "True": True,
  │ "a": 'b'}
   ╭────
 1 │ {% for x in a %}{{ x }}{% endfor %}{{ y|default:x }}
   ·                                                 ┬
   ·                                                 ╰── key
   ╰────
""")
    assert_render_error(
        template="{% for x in a %}{{ x }}{% endfor %}{{ y|default:x }}",
        context={"a": "b"},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )
