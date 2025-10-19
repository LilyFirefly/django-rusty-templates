import pytest
from django.template import engines
from django.template.exceptions import TemplateSyntaxError
from django.utils.translation import override
from hypothesis import given
from hypothesis.strategies import (
    lists,
    one_of,
    none,
    floats,
    booleans,
    integers,
    text,
    tuples,
    just,
    characters,
)


def test_render_if_true(assert_render):
    template = "{% if foo %}{{ foo }}{% endif %}"
    foo = "Foo"
    assert_render(template=template, context={"foo": foo}, expected=foo)


def test_render_if_false(assert_render):
    template = "{% if foo %}{{ foo }}{% endif %}"
    assert_render(template=template, context={}, expected="")


def test_render_elif(assert_render):
    template = "{% if False %}foo{% elif True %}bar{% else %}baz{% endif %}"
    assert_render(template=template, context={}, expected="bar")


def test_render_if_true_literal(assert_render):
    template = "{% if True %}foo{% endif %}"
    assert_render(template=template, context={}, expected="foo")


def test_render_translated_literal(template_engine):
    template = "{% if _('Welcome') %}foo{% endif %}"
    template_obj = template_engine.from_string(template)

    with override("de"):
        assert template_obj.render({}) == "foo"


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0])
def test_render_and(a, b, assert_render):
    template = "{% if a and b %}foo{% else %}bar{% endif %}"
    expected = "foo" if a and b else "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


def test_render_and_literals(assert_render):
    template = """{% if a and "b" and 'c' and 1 and 2.0 %}foo{% endif %}"""
    assert_render(template=template, context={"a": "a"}, expected="foo")


def test_render_or_literals(assert_render):
    template = """{% if a or "" or '' or 0 or 0.0 %}foo{% endif %}"""
    assert_render(template=template, context={"a": ""}, expected="")


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0])
def test_render_or(a, b, assert_render):
    template = "{% if a or b %}foo{% else %}bar{% endif %}"
    expected = "foo" if a or b else "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0])
def test_render_not(a, assert_render):
    template = "{% if not a %}foo{% else %}bar{% endif %}"
    expected = "foo" if not a else "bar"
    assert_render(template=template, context={"a": a}, expected=expected)


def compare(op, left, right):
    try:
        match op:
            case "==":
                return left == right
            case "!=":
                return left != right
            case "<":
                return left < right
            case ">":
                return left > right
            case "<=":
                return left <= right
            case ">=":
                return left >= right
    except TypeError:
        return False


class Float:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this == other

    def __ne__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this != other

    def __lt__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this < other

    def __gt__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this > other

    def __le__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this <= other

    def __ge__(self, other):
        this = float(self.value)
        if isinstance(other, Float):
            other = float(other.value)
        return this >= other


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_op_var_var(a, b, op, assert_render):
    template = f"{{%if a {op} b %}}truthy{{% else %}}falsey{{% endif %}}"
    expected = "truthy" if compare(op, a, b) else "falsey"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("b", ["foo", "", 1, 0, 1.5, -3.7])
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_op_var_literal(a, b, op, assert_render):
    template = f"{{%if a {op} {b!r} %}}truthy{{% else %}}falsey{{% endif %}}"
    expected = "truthy" if compare(op, a, b) else "falsey"
    assert_render(template=template, context={"a": a}, expected=expected)


@pytest.mark.parametrize("a", ["foo", "", 1, 0, 1.5, -3.7])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0])
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_op_literal_var(a, b, op, assert_render):
    template = f"{{%if {a!r} {op} b %}}truthy{{% else %}}falsey{{% endif %}}"
    expected = "truthy" if compare(op, a, b) else "falsey"
    assert_render(template=template, context={"b": b}, expected=expected)


@pytest.mark.parametrize(
    "a",
    [
        "foo",
        "",
        1,
        0,
        1.5,
        -3.7,
        10**310,
        -(10**310),
        Float("1.0e310"),
        Float("-1.0e310"),
    ],
)
@pytest.mark.parametrize(
    "b",
    [
        "foo",
        "",
        1,
        0,
        1.5,
        -3.7,
        10**310,
        -(10**310),
        Float("1.0e310"),
        Float("-1.0e310"),
    ],
)
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_op_literal_literal(a, b, op, assert_render):
    template = f"{{% if {a!r} {op} {b!r} %}}truthy{{% else %}}falsey{{% endif %}}"
    expected = "truthy" if compare(op, a, b) else "falsey"
    assert_render(template=template, context={}, expected=expected)


@pytest.mark.parametrize("a", ["foo", 1, "", 0])
@pytest.mark.parametrize("b", ["foobar", "bar", [1, 2], ["foobar", 1]])
def test_render_in(a, b, assert_render):
    template = "{% if a in b %}foo{% else %}bar{% endif %}"
    try:
        expected = "foo" if a in b else "bar"
    except TypeError:
        expected = "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


@pytest.mark.parametrize("a", ["foo", 1, "", 0])
@pytest.mark.parametrize("b", ["foobar", "bar", [1, 2], ["foobar", 1]])
def test_render_not_in(a, b, assert_render):
    template = "{% if a not in b %}foo{% else %}bar{% endif %}"
    try:
        expected = "foo" if a not in b else "bar"
    except TypeError:
        expected = "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0, None])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0, None])
def test_render_is(a, b, assert_render):
    template = "{% if a is b %}foo{% else %}bar{% endif %}"
    expected = "foo" if a is b else "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


@pytest.mark.parametrize("a", [True, False, "foo", 1, "", 0, None])
@pytest.mark.parametrize("b", [True, False, "foo", 1, "", 0, None])
def test_render_is_not(a, b, assert_render):
    template = "{% if a is not b %}foo{% else %}bar{% endif %}"
    expected = "foo" if a is not b else "bar"
    assert_render(template=template, context={"a": a, "b": b}, expected=expected)


def test_invalid_and_position():
    template = "{% if and %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'and' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'and' in this position
   ╭────
 1 │ {% if and %}{{ foo }}{% endif %}
   ·       ─┬─
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_or_position():
    template = "{% if or %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'or' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'or' in this position
   ╭────
 1 │ {% if or %}{{ foo }}{% endif %}
   ·       ─┬
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_no_condition():
    template = "{% if %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Unexpected end of expression in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Missing boolean expression
   ╭────
 1 │ {% if %}{{ foo }}{% endif %}
   · ────┬───
   ·     ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_end_of_expression():
    template = "{% if not %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Unexpected end of expression in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected end of expression
   ╭────
 1 │ {% if not %}{{ foo }}{% endif %}
   ·       ─┬─
   ·        ╰── after this
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_in_position():
    template = "{% if in %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'in' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'in' in this position
   ╭────
 1 │ {% if in %}{{ foo }}{% endif %}
   ·       ─┬
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_not_in_position():
    template = "{% if not in %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'not in' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'not in' in this position
   ╭────
 1 │ {% if not in %}{{ foo }}{% endif %}
   ·       ───┬──
   ·          ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_is_position():
    template = "{% if is %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'is' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'is' in this position
   ╭────
 1 │ {% if is %}{{ foo }}{% endif %}
   ·       ─┬
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_is_not_position():
    template = "{% if is not %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Not expecting 'is not' in this position in if tag."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Not expecting 'is not' in this position
   ╭────
 1 │ {% if is not %}{{ foo }}{% endif %}
   ·       ───┬──
   ·          ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_no_operator():
    template = "{% if foo bar spam %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Unused 'bar' at end of if expression."

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unused expression 'bar' in if tag
   ╭────
 1 │ {% if foo bar spam %}{{ foo }}{% endif %}
   ·           ─┬─
   ·            ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_invalid_token():
    template = "{% if foo 'bar %}{{ foo }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Could not parse the remainder: ''bar' from ''bar'"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a complete string literal
   ╭────
 1 │ {% if foo 'bar %}{{ foo }}{% endif %}
   ·           ──┬─
   ·             ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


VALID_VARIABLE_NAMES = text(
    alphabet=characters(max_codepoint=91, categories=["Ll", "Lu", "Nd"]),
    min_size=1,
).filter(lambda s: not s[0].isdigit())


VALID_ATOM = one_of(
    none(),
    booleans(),
    floats(),
    integers(),
    text().map("'{}'".format),
    text().map('"{}"'.format),
    VALID_VARIABLE_NAMES,
)

VALID_DEFAULT = tuples(VALID_VARIABLE_NAMES, VALID_ATOM).map(
    lambda t: f"{t[0]}|default:{t[1]}"
)

VALID_ATOM = one_of(VALID_ATOM, VALID_DEFAULT)

VALID_ATOM = one_of(VALID_ATOM, VALID_ATOM.map("not {}".format))

VALID_OPERATOR = one_of(
    just("and"),
    just("or"),
    just("=="),
    just("!="),
    just("<"),
    just(">"),
    just("<="),
    just(">="),
    just("in"),
    just("not in"),
    just("is"),
    just("is not"),
)


VALID_ATOM_NO_INTEGERS = one_of(
    none(),
    booleans(),
    floats(),
    text().map("'{}'".format),
    text().map('"{}"'.format),
    VALID_VARIABLE_NAMES,
)

VALID_OPERATOR_NO_IS = one_of(
    just("and"),
    just("or"),
    just("=="),
    just("!="),
    just("<"),
    just(">"),
    just("<="),
    just(">="),
    just("in"),
    just("not in"),
)


def to_template(parts):
    flat = []
    for var, op in parts:
        flat.append(str(var))
        flat.append(str(op))

    condition = " ".join(flat[:-1])
    return f"{{% if {condition} %}}truthy{{% else %}}falsey{{% endif %}}"


@given(lists(tuples(VALID_ATOM, VALID_OPERATOR_NO_IS)).map(to_template))
def test_render_same_result_no_is(template):
    try:
        django_template = engines["django"].from_string(template)
    except TemplateSyntaxError:
        with pytest.raises(TemplateSyntaxError):
            engines["rusty"].from_string(template)
    else:
        rust_template = engines["rusty"].from_string(template)

        context = {}
        assert rust_template.render(context) == django_template.render(context)


@given(lists(tuples(VALID_ATOM_NO_INTEGERS, VALID_OPERATOR)).map(to_template))
def test_render_same_result_no_integers(template):
    # We can't test `is` with integers without triggering failures due to Python's
    # small integer cache optimisation.
    try:
        django_template = engines["django"].from_string(template)
    except TemplateSyntaxError:
        with pytest.raises(TemplateSyntaxError):
            engines["rusty"].from_string(template)
    else:
        rust_template = engines["rusty"].from_string(template)

        context = {}
        assert rust_template.render(context) == django_template.render(context)


def test_render_none_is_not_none_equal_none():
    template = "{% if None is not None == None %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_render_none_equal_none_is_not_not_none():
    template = "{% if None == None is not not None %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_number_less_than_false():
    template = "{% if 1 < False %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_escaped_unicode_escape():
    template = "{% if '\\\x80' %}truthy{% else %}falsey{% endif %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_incomplete_escape():
    template = "{% if '\\ %}truthy{% else %}falsey{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Could not parse the remainder: ''\\' from ''\\'"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a complete string literal
   ╭────
 1 │ {% if '\\ %}truthy{% else %}falsey{% endif %}
   ·       ─┬
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_zero_less_than_not_none():
    template = "{% if 0.0 < not None %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_zero_not_in_zero():
    template = "{% if 0.0 not in 0.0 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_text_is_not_not_variable():
    template = (
        '{% if "õeS" is not not WQWJXO52RWIA0D %}truthy{% else %}falsey{% endif %}'
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_none_equal_none_not_in_zero():
    template = "{% if None == None not in 0.0 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_if_tag_split_by_newline():
    template = "{% if '\n' %}truthy{% else %}falsey{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 2: 'else'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag else
   ╭─[2:11]
 1 │ {% if '
 2 │ ' %}truthy{% else %}falsey{% endif %}
   ·           ─────┬────
   ·                ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_var_lte_var():
    template = "{% if B <= A %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_variable_filter_argument_negative_number():
    template = "{% if a|default:-22569 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_unexpected_tag_elif():
    template = "{% elif foo %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 1: 'elif'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag elif
   ╭────
 1 │ {% elif foo %}
   · ───────┬──────
   ·        ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_tag_else():
    template = "{% else %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 1: 'else'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag else
   ╭────
 1 │ {% else %}
   · ─────┬────
   ·      ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_unexpected_tag_endif():
    template = "{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert (
        str(exc_info.value)
        == "Invalid block tag on line 1: 'endif'. Did you forget to register or load this tag?"
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Unexpected tag endif
   ╭────
 1 │ {% endif %}
   · ─────┬─────
   ·      ╰── unexpected tag
   ╰────
"""
    assert str(exc_info.value) == expected


def test_false_not_equal_var():
    template = "{% if False != inf %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_var_not_equal_false():
    template = "{% if inf != False %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_false_not_equal_default_var():
    template = "{% if False != foo|default:bar %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_default_var_not_equal_false():
    template = "{% if foo|default:bar != False %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


@pytest.mark.parametrize("a", [None, True, False])
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_not_equal_not_default(a, op):
    template = (
        f"{{% if {a} {op} not foo|default:foo %}}truthy{{% else %}}falsey{{% endif %}}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    expected = "truthy" if compare(op, a, False) else "falsey"

    assert django_template.render({"a": a}) == expected
    assert rust_template.render({"a": a}) == expected


def test_var_equal_var():
    template = "{% if A == A %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_default_equal_default():
    template = (
        "{% if foo|default:foo == bar|default:bar %}truthy{% else %}falsey{% endif %}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_not_default_var():
    template = "{% if not foo|default:foo %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_not_none_eq_default_var():
    template = "{% if not None == foo|default:foo %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_truthy_op_not_default(op):
    template = f"{{% if None == None {op} not A|default:A %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    expected = "truthy" if compare(op, True, False) else "falsey"

    assert django_template.render() == expected
    assert rust_template.render() == expected


@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_render_falsey_op_not_default(op):
    template = f"{{% if None != None {op} not A|default:A %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    expected = "truthy" if compare(op, False, False) else "falsey"

    assert django_template.render() == expected
    assert rust_template.render() == expected


def test_render_none_eq_none_is_var():
    template = "{% if None == None is foo %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_render_default_or_1():
    template = "{% if A|default:A or 1 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_render_none_or_default_or_1():
    template = "{% if None or A|default:A or 1 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_render_default_and_none_or_not_none():
    template = (
        "{% if A|default:inf and None or not None %}truthy{% else %}falsey{% endif %}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


@pytest.mark.parametrize("a", ["foo", "bar"])
@pytest.mark.parametrize("b", ["foo", "bar"])
@pytest.mark.parametrize("a_format", ["variable", "repr", "safe"])
@pytest.mark.parametrize("b_format", ["variable", "repr", "safe"])
@pytest.mark.parametrize("op", ["==", "!=", "<", ">", "<=", ">="])
def test_comparison_autoescape_off(op, a, b, a_format, b_format):
    context = {"a": a, "b": b}
    expected = "truthy" if compare(op, a, b) else "falsey"

    if a_format == "repr":
        a = repr(a)
    elif a_format == "safe":
        a = "a|safe"
    else:
        a = "a"

    if b_format == "repr":
        b = repr(b)
    elif b_format == "safe":
        b = "b|safe"
    else:
        b = "b"

    template = f"{{% autoescape off %}}{{% if {a} {op} {b} %}}truthy{{% else %}}falsey{{% endif %}}{{% endautoescape %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render(context) == expected
    assert rust_template.render(context) == expected


def test_string_content_autoescape_off():
    template = "{% autoescape off %}{% if 'foo' %}truthy{% else %}falsey{% endif %}{% endautoescape %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


@pytest.mark.parametrize("a", [repr("foo"), False, "missing"])
@pytest.mark.parametrize("op", ["==", "!="])
def test_op_not(a, op):
    expected = "truthy" if compare(op, a, False) else "falsey"
    template = f"{{% if {a} {op} not 'bar' %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == expected
    assert rust_template.render({}) == expected


@pytest.mark.parametrize("op", ["==", "!="])
def test_comparison_op_not(op):
    expected = "truthy" if compare(op, True, False) else "falsey"
    template = (
        f"{{% if 'foo' == 'foo' {op} not 'bar' %}}truthy{{% else %}}falsey{{% endif %}}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == expected
    assert rust_template.render({}) == expected


@pytest.mark.parametrize("op", ["<", ">", "<=", ">="])
def test_missing_op_other(op):
    template = f"{{% if foo {op} 2 %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


@pytest.mark.parametrize("number", [2, 2.0])
@pytest.mark.parametrize("op", ["==", "<", ">", "<=", ">="])
@pytest.mark.parametrize("boolean", [True, False])
def test_number_op_boolean(number, op, boolean):
    expected = "truthy" if compare(op, number, boolean) else "falsey"
    boolean = not boolean
    template = (
        f"{{% if {number} {op} not {boolean} %}}truthy{{% else %}}falsey{{% endif %}}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == expected
    assert rust_template.render({}) == expected


@pytest.mark.parametrize("op", ["<", ">", "<=", ">=", "in", "not in", "is", "is not"])
def test_op_with_error(op):
    template = f"{{% if missing|default:missing {op} 'foo' %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


@pytest.mark.parametrize("value", [1, 1.0])
def test_variable_in_value(value):
    template = f"{{% if foo in {value} %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": "foo"}) == "falsey"
    assert rust_template.render({"foo": "foo"}) == "falsey"


@pytest.mark.parametrize("value", ["foo", 1, 1.0])
def test_missing_in_value(value):
    template = f"{{% if missing in {value} %}}truthy{{% else %}}falsey{{% endif %}}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": "foo"}) == "falsey"
    assert rust_template.render({"foo": "foo"}) == "falsey"


def test_value_in_missing():
    template = "{% if foo in missing %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": "foo"}) == "falsey"
    assert rust_template.render({"foo": "foo"}) == "falsey"


def test_int_in_string():
    template = "{% if 1 in 'foo' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_float_in_string():
    template = "{% if 1.0 in 'foo' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_int_in_variable():
    template = "{% if 1 in foo %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": "foo"}) == "falsey"
    assert rust_template.render({"foo": "foo"}) == "falsey"


def test_float_in_variable():
    template = "{% if 1.0 in foo %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": "foo"}) == "falsey"
    assert rust_template.render({"foo": "foo"}) == "falsey"


def test_string_in_int():
    template = "{% if 'foo' in 1 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_string_in_float():
    template = "{% if 'foo' in 1.0 %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_string_in_variable():
    template = "{% if 'foo' in bar %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"bar": "bar"}) == "falsey"
    assert rust_template.render({"bar": "bar"}) == "falsey"


def test_missing_is_missing():
    template = "{% if foo is bar %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_missing_is_variable():
    template = "{% if foo is bar %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"bar": ""}) == "falsey"
    assert rust_template.render({"bar": ""}) == "falsey"


def test_variable_is_missing():
    template = "{% if foo is bar %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": ""}) == "falsey"
    assert rust_template.render({"foo": ""}) == "falsey"


def test_string_is_string():
    template = "{% if '' is '' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": ""}) == "falsey"
    assert rust_template.render({"foo": ""}) == "falsey"


def test_expr_is_string():
    template = "{% if 'foo' == 'foo' is 'bar' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "falsey"
    assert rust_template.render({}) == "falsey"


def test_expr_is_not_string():
    template = "{% if 'foo' == 'foo' is not 'bar' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_string_is_not_expr():
    template = "{% if 'foo' is not not 'bar' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_bool_is_not_expr():
    template = "{% if True is not not 'bar' %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_string_is_not_missing():
    template = (
        "{% if 'foo' is not not bar|default:bar %}truthy{% else %}falsey{% endif %}"
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_not_inf_or_not_none():
    template = "{% if not A|default:inf or not None %}truthy{% else %}falsey{% endif %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truthy"
    assert rust_template.render({}) == "truthy"


def test_if_forloop_first():
    template = "{% for x in y %}{% if forloop.first %}truthy{% else %}falsey{% endif %}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == "truthyfalsey"
    assert rust_template.render({"y": "12"}) == "truthyfalsey"


def test_if_not_bool():
    template = "{% for x in y %}{% if not forloop.first %}truthy{% else %}falsey{% endif %}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == "falseytruthy"
    assert rust_template.render({"y": "12"}) == "falseytruthy"


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("forloop.first", "forloop.first", "tt"),
        ("forloop.first", "forloop.last", "ff"),
        ("forloop.first", True, "tf"),
        ("forloop.first", False, "ft"),
        ("forloop.first", 1, "tf"),
        ("forloop.first", 0, "ft"),
        ("forloop.first", 1.0, "tf"),
        ("forloop.first", 0.0, "ft"),
        ("forloop.first", 2, "ff"),
        ("forloop.first", -1, "ff"),
        ("forloop.first", 2.0, "ff"),
        ("forloop.first", -1.0, "ff"),
        (True, "forloop.first", "tf"),
        (False, "forloop.first", "ft"),
        (1, "forloop.first", "tf"),
        (0, "forloop.first", "ft"),
        (1.0, "forloop.first", "tf"),
        (0.0, "forloop.first", "ft"),
        (2, "forloop.first", "ff"),
        (-1, "forloop.first", "ff"),
        (2.0, "forloop.first", "ff"),
        (-1.0, "forloop.first", "ff"),
    ],
)
def test_if_eq_bool(first, second, expected):
    template = (
        "{%% for x in y %%}{%% if %s == %s %%}t{%% else %%}f{%% endif %%}{%% endfor %%}"
        % (first, second)
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == expected
    assert rust_template.render({"y": "12"}) == expected


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("forloop.first", "forloop.first", "ff"),
        ("forloop.first", "forloop.last", "ft"),
        ("forloop.first", True, "ft"),
        ("forloop.first", False, "ff"),
        ("forloop.first", 1, "ft"),
        ("forloop.first", 0, "ff"),
        ("forloop.first", 1.0, "ft"),
        ("forloop.first", 0.0, "ff"),
        ("forloop.first", 256, "tt"),
        ("forloop.first", -1, "ff"),
        ("forloop.first", 256.0, "tt"),
        ("forloop.first", -1.0, "ff"),
        (True, "forloop.first", "ff"),
        (False, "forloop.first", "tf"),
        (1, "forloop.first", "ff"),
        (0, "forloop.first", "tf"),
        (1.0, "forloop.first", "ff"),
        (0.0, "forloop.first", "tf"),
        (256, "forloop.first", "ff"),
        (-1, "forloop.first", "tt"),
        (256.0, "forloop.first", "ff"),
        (-1.0, "forloop.first", "tt"),
    ],
)
def test_if_lt_bool(first, second, expected):
    template = (
        "{%% for x in y %%}{%% if %s < %s %%}t{%% else %%}f{%% endif %%}{%% endfor %%}"
        % (first, second)
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == expected
    assert rust_template.render({"y": "12"}) == expected


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("forloop.first", "forloop.first", "tt"),
        ("forloop.first", "forloop.last", "ft"),
        ("forloop.first", True, "tt"),
        ("forloop.first", False, "ft"),
        ("forloop.first", 1, "tt"),
        ("forloop.first", 0, "ft"),
        ("forloop.first", 1.0, "tt"),
        ("forloop.first", 0.0, "ft"),
        ("forloop.first", 256, "tt"),
        ("forloop.first", -1, "ff"),
        ("forloop.first", 256.0, "tt"),
        ("forloop.first", -1.0, "ff"),
        (True, "forloop.first", "tf"),
        (False, "forloop.first", "tt"),
        (1, "forloop.first", "tf"),
        (0, "forloop.first", "tt"),
        (1.0, "forloop.first", "tf"),
        (0.0, "forloop.first", "tt"),
        (256, "forloop.first", "ff"),
        (-1, "forloop.first", "tt"),
        (256.0, "forloop.first", "ff"),
        (-1.0, "forloop.first", "tt"),
    ],
)
def test_if_lte_bool(first, second, expected):
    template = (
        "{%% for x in y %%}{%% if %s <= %s %%}t{%% else %%}f{%% endif %%}{%% endfor %%}"
        % (first, second)
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == expected
    assert rust_template.render({"y": "12"}) == expected


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("forloop.first", "forloop.first", "ff"),
        ("forloop.first", "forloop.last", "tf"),
        ("forloop.first", True, "ff"),
        ("forloop.first", False, "tf"),
        ("forloop.first", 1, "ff"),
        ("forloop.first", 0, "tf"),
        ("forloop.first", 1.0, "ff"),
        ("forloop.first", 0.0, "tf"),
        ("forloop.first", 256, "ff"),
        ("forloop.first", -1, "tt"),
        ("forloop.first", 256.0, "ff"),
        ("forloop.first", -1.0, "tt"),
        (True, "forloop.first", "ft"),
        (False, "forloop.first", "ff"),
        (1, "forloop.first", "ft"),
        (0, "forloop.first", "ff"),
        (1.0, "forloop.first", "ft"),
        (0.0, "forloop.first", "ff"),
        (256, "forloop.first", "tt"),
        (-1, "forloop.first", "ff"),
        (256.0, "forloop.first", "tt"),
        (-1.0, "forloop.first", "ff"),
    ],
)
def test_if_gt_bool(first, second, expected):
    template = (
        "{%% for x in y %%}{%% if %s > %s %%}t{%% else %%}f{%% endif %%}{%% endfor %%}"
        % (first, second)
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == expected
    assert rust_template.render({"y": "12"}) == expected


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("forloop.first", "forloop.first", "tt"),
        ("forloop.first", "forloop.last", "tf"),
        ("forloop.first", True, "tf"),
        ("forloop.first", False, "tt"),
        ("forloop.first", 1, "tf"),
        ("forloop.first", 0, "tt"),
        ("forloop.first", 1.0, "tf"),
        ("forloop.first", 0.0, "tt"),
        ("forloop.first", 256, "ff"),
        ("forloop.first", -1, "tt"),
        ("forloop.first", 256.0, "ff"),
        ("forloop.first", -1.0, "tt"),
        (True, "forloop.first", "tt"),
        (False, "forloop.first", "ft"),
        (1, "forloop.first", "tt"),
        (0, "forloop.first", "ft"),
        (1.0, "forloop.first", "tt"),
        (0.0, "forloop.first", "ft"),
        (256, "forloop.first", "tt"),
        (-1, "forloop.first", "ff"),
        (256.0, "forloop.first", "tt"),
        (-1.0, "forloop.first", "ff"),
    ],
)
def test_if_gte_bool(first, second, expected):
    template = (
        "{%% for x in y %%}{%% if %s >= %s %%}t{%% else %%}f{%% endif %%}{%% endfor %%}"
        % (first, second)
    )
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"y": "12"}) == expected
    assert rust_template.render({"y": "12"}) == expected


def test_if_not_numeric():
    template = "{% if 1.1.1 %}foo{% endif %}"

    django_template = engines["django"].from_string(template)

    assert django_template.render({"1": {"1": {"1": "bar"}}}) == "foo"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Invalid numeric literal
   ╭────
 1 │ {% if 1.1.1 %}foo{% endif %}
   ·       ──┬──
   ·         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_if_invalid_variable():
    template = "{% if a- %}foo{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    expected = "Could not parse the remainder: '-' from 'a-'"
    assert str(exc_info.value) == expected

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% if a- %}foo{% endif %}
   ·       ─┬
   ·        ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_if_invalid_content():
    template = "{% if a %}{{ a- }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    expected = "Could not parse the remainder: '-' from 'a-'"
    assert str(exc_info.value) == expected

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% if a %}{{ a- }}{% endif %}
   ·              ─┬
   ·               ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_if_invalid_content_tag():
    template = "{% if a %}{% if a- %}{% endif %}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    expected = "Could not parse the remainder: '-' from 'a-'"
    assert str(exc_info.value) == expected

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% if a %}{% if a- %}{% endif %}{% endif %}
   ·                 ─┬
   ·                  ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_elif_invalid_content():
    template = "{% if a %}{% elif b %}{{ a- }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    expected = "Could not parse the remainder: '-' from 'a-'"
    assert str(exc_info.value) == expected

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% if a %}{% elif b %}{{ a- }}{% endif %}
   ·                          ─┬
   ·                           ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_else_invalid_content():
    template = "{% if a %}{% else %}{{ a- }}{% endif %}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    expected = "Could not parse the remainder: '-' from 'a-'"
    assert str(exc_info.value) == expected

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {% if a %}{% else %}{{ a- }}{% endif %}
   ·                        ─┬
   ·                         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected
