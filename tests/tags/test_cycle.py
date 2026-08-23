from inline_snapshot import snapshot


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
