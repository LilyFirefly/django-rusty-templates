from inline_snapshot import snapshot

# Some tests taken from Django tests suite for cycle tag:
# https://github.com/django/django/blob/main/tests/template_tests/syntax_tests/test_cycle.py


def test_cycle_literals_in_loop(assert_render):
    template = '{% for item in items %}{% cycle "odd" "even" %}{% endfor %}'
    context = {"items": range(4)}
    expected = "oddevenoddeven"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )


def test_cycle_literals_with_loop_value(assert_render):
    template = "{% for item in items %}{% cycle 'a' 'b' %}{{ item }},{% endfor %}"
    context = {"items": range(5)}
    expected = "a0,b1,a2,b3,a4,"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )


def test_cycle_context_variables_in_loop(assert_render):
    template = "{% for item in items %}{% cycle first second %}{{ item }},{% endfor %}"
    context = {
        "items": range(5),
        "first": "a",
        "second": "b",
    }
    expected = "a0,b1,a2,b3,a4,"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )


def test_cycle_missing_context_variable_in_loop(assert_render):
    assert_render(
        template=("{% for item in items %}{% cycle missing 'b' %}{% endfor %}"),
        context={"items": range(2)},
        expected="b",
    )


def test_cycle_filtered_variable_in_loop(assert_render):
    template = "{% for item in items %}{% cycle first|lower second %}{% endfor %}"
    context = {
        "items": range(4),
        "first": "A",
        "second": "2",
    }
    expected = "a2a2"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )


def test_cycle_tags_advance_independently(assert_render):
    template = (
        "{% for item in items %}{% cycle 'a' 'b' %}{% cycle 'x' 'y' 'z' %}{% endfor %}"
    )
    context = {"items": range(6)}
    expected = "axbyazbxaybz"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )


def test_cycle_missing_argument_error(assert_parse_error):
    assert_parse_error(
        template="{% cycle %}",
        django_message="'cycle' tag requires at least two arguments",
        rusty_message=snapshot("""\
  × Expected an argument
   ╭────
 1 │ {% cycle %}
   ·         ▲
   ·         ╰── here
   ╰────
"""),
    )


def test_cycle_comma_separated_values_error(assert_parse_error):
    assert_parse_error(
        template="{% cycle a,b,c as foo %}{% cycle bar %}",
        django_message="Could not parse the remainder: ',b,c' from 'a,b,c'",
        rusty_message=snapshot("""\
  × Could not parse the remainder
   ╭────
 1 │ {% cycle a,b,c as foo %}{% cycle bar %}
   ·           ──┬─
   ·             ╰── here
   ╰────
"""),
    )


def test_unknown_named_cycle_error(assert_parse_error):
    assert_parse_error(
        template="{% cycle missing %}",
        django_message="No named cycles in template. 'missing' is not defined",
        rusty_message=snapshot("""\
  × Unknown named cycle 'missing'
   ╭────
 1 │ {% cycle missing %}
   ·          ───┬───
   ·             ╰── unknown cycle
   ╰────
  help: Define the named cycle earlier using the 'as' form.
"""),
    )


def test_named_cycle(assert_render):
    assert_render(
        template="{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}",
        context={},
        expected="ab",
    )


def test_named_cycle_references_share_state(assert_render):
    template = (
        "{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}{% cycle abc %}{% cycle abc %}"
    )

    assert_render(
        template=template,
        context={},
        expected="abca",
    )


def test_named_cycle_sets_context_variable(assert_render):
    assert_render(
        template="{% cycle 'a' 'b' as current %}{{ current }}",
        context={},
        expected="aa",
    )


def test_named_cycle_sets_missing_context_variable_to_empty(assert_render):
    assert_render(
        template=(
            "{% cycle missing 'b' as current %}"
            "[{{ current }}]"
            "{% cycle current %}"
            "[{{ current }}]"
        ),
        context={},
        expected="[]b[b]",
    )


def test_cycle_value_resolution_error(assert_render_error):
    def broken():
        raise ValueError("cycle resolution error")

    assert_render_error(
        template="{% cycle broken 'fallback' %}",
        context={"broken": broken},
        exception=ValueError,
        django_message=snapshot("cycle resolution error"),
        rusty_message=snapshot("""\
  × cycle resolution error
   ╭────
 1 │ {% cycle broken 'fallback' %}
   ·          ───┬──
   ·             ╰── here
   ╰────
"""),
    )


def test_cycle_value_rendering_error(assert_render_error):
    class Unstringable:
        def __str__(self):
            raise ValueError("cycle rendering error")

    assert_render_error(
        template="{% cycle value 'fallback' %}",
        context={"value": Unstringable()},
        exception=ValueError,
        django_message=snapshot("cycle rendering error"),
        rusty_message=snapshot("cycle rendering error"),
    )


def test_named_cycle_silent(assert_render):
    template = (
        "{% cycle 'a' 'b' 'c' as abc silent %}"
        "{% cycle abc %}"
        "{% cycle abc %}"
        "{% cycle abc %}"
        "{% cycle abc %}"
    )

    assert_render(
        template=template,
        context={},
        expected="",
    )


def test_silent_named_cycle_sets_context_variable(assert_render):
    template = (
        "{% for item in items %}"
        "{% cycle 'a' 'b' 'c' as abc silent %}"
        "{{ abc }}{{ item }}"
        "{% endfor %}"
    )

    assert_render(
        template=template,
        context={"items": [1, 2, 3, 4]},
        expected="a1b2c3a4",
    )


def test_invalid_cycle_flag_error(assert_parse_error):
    assert_parse_error(
        template="{% cycle 'a' 'b' 'c' as abc invalid_flag %}",
        django_message=(
            "Only 'silent' flag is allowed after cycle's name, not 'invalid_flag'."
        ),
        rusty_message=snapshot("""\
  × Invalid flag 'invalid_flag' after cycle name
   ╭────
 1 │ {% cycle 'a' 'b' 'c' as abc invalid_flag %}
   ·                             ──────┬─────
   ·                                   ╰── invalid flag
   ╰────
  help: Only the 'silent' flag is allowed here.
"""),
    )


def test_named_cycle_autoescapes_values(assert_render):
    assert_render(
        template="{% cycle first second as current %} &amp; {% cycle current %}",
        context={
            "first": "A & B",
            "second": "C & D",
        },
        expected="A &amp; B &amp; C &amp; D",
    )


def test_named_cycle_respects_autoescape_off(assert_render):
    assert_render(
        template=(
            "{% autoescape off %}"
            "{% cycle first second as current %}"
            "{% cycle current %}"
            "{% endautoescape %}"
        ),
        context={
            "first": "<",
            "second": ">",
        },
        expected="<>",
    )


def test_named_cycle_preserves_safe_value(assert_render):
    assert_render(
        template=("{% cycle first|safe second as current %}{% cycle current %}"),
        context={
            "first": "<",
            "second": ">",
        },
        expected="<&gt;",
    )


def test_named_cycle_can_be_called_silent(assert_render):
    assert_render(
        template="{% cycle 'a' 'b' as silent %}{% cycle silent %}",
        context={},
        expected="ab",
    )


def test_unknown_named_cycle_after_definition_error(assert_parse_error):
    assert_parse_error(
        template=("{% cycle 'a' 'b' as existing %}{% cycle missing %}"),
        django_message="Named cycle 'missing' does not exist",
        rusty_message=snapshot("""\
  × Unknown named cycle 'missing'
   ╭────
 1 │ {% cycle 'a' 'b' as existing %}{% cycle missing %}
   ·                                         ───┬───
   ·                                            ╰── unknown cycle
   ╰────
  help: Define the named cycle earlier using the 'as' form.
"""),
    )


def test_named_cycle_advances_across_multiple_references(assert_render):
    assert_render(
        template=("{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}{% cycle abc %}"),
        context={},
        expected="abc",
    )


def test_named_cycle_context_variables(assert_render):
    assert_render(
        template="{% cycle one two as current %}{% cycle current %}",
        context={"one": "1", "two": "2"},
        expected="12",
    )


def test_named_cycle_filtered_variable(assert_render):
    assert_render(
        template="{% cycle one|lower two as current %}{% cycle current %}",
        context={"one": "A", "two": "2"},
        expected="a2",
    )


def test_silent_named_cycle_suppresses_output_in_loop(assert_render):
    assert_render(
        template=(
            "{% for item in items %}"
            "{% cycle 'a' 'b' 'c' as abc silent %}"
            "{{ item }}"
            "{% endfor %}"
        ),
        context={"items": [1, 2, 3, 4]},
        expected="1234",
    )


def test_silent_named_cycle_variable_available_in_include(
    assert_render,
    template_engine,
):
    included_template = template_engine.from_string("{{ abc }}")

    assert_render(
        template=(
            "{% for item in items %}"
            "{% cycle 'a' 'b' 'c' as abc silent %}"
            "{% include included_template %}"
            "{% endfor %}"
        ),
        context={
            "items": [1, 2, 3, 4],
            "included_template": included_template,
        },
        expected="abca",
    )


def test_cycle_single_value_as_syntax(assert_render):
    assert_render(
        template="{% cycle value as current %}",
        context={"value": "<"},
        expected="&lt;",
    )


def test_named_cycle_escapes_each_value(assert_render):
    assert_render(
        template="{% cycle first second as current %}{% cycle current %}",
        context={"first": "<", "second": ">"},
        expected="&lt;&gt;",
    )


def test_unknown_named_cycle_inside_loop_error(assert_parse_error):
    assert_parse_error(
        template=(
            "{% cycle 'a' 'b' 'c' as cycler silent %}"
            "{% for item in items %}"
            "{% cycle undefined %}{{ cycler }}"
            "{% endfor %}"
        ),
        django_message="Named cycle 'undefined' does not exist",
        rusty_message=snapshot("""\
  × Unknown named cycle 'undefined'
   ╭────
 1 │ {% cycle 'a' 'b' 'c' as cycler silent %}{% for item in items %}{% cycle undefined %}{{ cycler }}{% endfor %}
   ·                                                                         ────┬────
   ·                                                                             ╰── unknown cycle
   ╰────
  help: Define the named cycle earlier using the 'as' form.
"""),
    )
