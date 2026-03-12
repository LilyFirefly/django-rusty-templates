from inline_snapshot import snapshot
import pytest
from django.template import engines
from django.template.base import VariableDoesNotExist
from django.template.exceptions import TemplateSyntaxError
from django.test import RequestFactory
from django.urls import resolve, NoReverseMatch


factory = RequestFactory()


def test_render_url(assert_render):
    template = "{% url 'home' %}"
    expected = "/"
    assert_render(template, {}, expected)


def test_render_url_variable(assert_render):
    assert_render(template="{% url home %}", context={"home": "home"}, expected="/")


def test_render_url_view_missing_as(assert_render):
    template = "{% url 'missing' as missing %}{{ missing }}"
    expected = ""
    assert_render(template, {}, expected)


def test_render_url_arg(assert_render):
    template = "{% url 'bio' 'lily' %}"
    expected = "/bio/lily/"
    assert_render(template, {}, expected)


def test_render_url_kwarg(assert_render):
    template = "{% url 'bio' username='lily' %}"
    expected = "/bio/lily/"
    assert_render(template, {}, expected)


def test_render_url_arg_as_variable(assert_render):
    template = "{% url 'bio' 'lily' as bio %}https://example.com{{ bio }}"
    expected = "https://example.com/bio/lily/"
    assert_render(template, {}, expected)


def test_render_url_kwarg_as_variable(assert_render):
    template = "{% url 'bio' username='lily' as bio %}https://example.com{{ bio }}"
    expected = "https://example.com/bio/lily/"
    assert_render(template, {}, expected)


def test_render_url_current_app_unset(assert_render):
    template = "{% url 'users:user' 'lily' %}"

    request = factory.get("/")

    expected = "/users/lily/"
    assert_render(template=template, context={}, request=request, expected=expected)


def test_render_url_as_variable(assert_render):
    template = "{% url 'users:user' as %}"

    request = factory.get("/")

    expected = "/users/lily/"
    assert_render(
        template=template, context={"as": "lily"}, request=request, expected=expected
    )


def test_render_url_as_variable_and_binding(assert_render):
    template = "{% url as 'lily' as user_url %}{{ user_url }}"

    request = factory.get("/")

    expected = "/users/lily/"
    assert_render(
        template=template,
        context={"as": "users:user"},
        request=request,
        expected=expected,
    )


def test_render_url_current_app(assert_render):
    template = "{% url 'users:user' 'lily' %}"

    request = factory.get("/")
    request.current_app = "members"

    expected = "/members/lily/"
    assert_render(template=template, context={}, request=request, expected=expected)


def test_render_url_current_app_kwargs(assert_render):
    template = "{% url 'users:user' username='lily' %}"

    request = factory.get("/")
    request.current_app = "members"

    expected = "/members/lily/"
    assert_render(template=template, context={}, request=request, expected=expected)


def test_render_url_current_app_resolver_match(assert_render):
    template = "{% url 'users:user' username='lily' %}"

    request = factory.get("/")
    request.resolver_match = resolve("/members/bryony/")

    expected = "/members/lily/"
    assert_render(template=template, context={}, request=request, expected=expected)


def test_parse_url_args_and_kwargs(template_engine):
    template = "{% url 'users:user' 'Alice' username='lily' %}"

    django_message = snapshot("Don't mix *args and **kwargs in call to reverse()!")
    rusty_message = snapshot("""\
  × Cannot mix arguments and keyword arguments
   ╭────
 1 │ {% url 'users:user' 'Alice' username='lily' %}
   · ───────────────────────┬──────────────────────
   ·                        ╰── here
   ╰────
""")

    if template_engine.name == "rusty":
        with pytest.raises(TemplateSyntaxError) as exc_info:
            template_engine.from_string(template)

        assert str(exc_info.value) == rusty_message
    else:
        template = template_engine.from_string(template)
        with pytest.raises(ValueError) as exc_info:
            template.render({})

        assert str(exc_info.value) == django_message


def test_render_url_view_name_error():
    template = "{% url foo.bar.1b.baz %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    with pytest.raises(NoReverseMatch) as django_error:
        django_template.render({"foo": {"bar": 1}})

    msg = "Reverse for '' not found. '' is not a valid view function or pattern name."
    assert django_error.value.args[0] == msg

    with pytest.raises(VariableDoesNotExist) as rust_error:
        rust_template.render({"foo": {"bar": 1}})

    expected = """\
  × Failed lookup for key [1b] in 1
   ╭────
 1 │ {% url foo.bar.1b.baz %}
   ·        ───┬─── ─┬
   ·           │     ╰── key
   ·           ╰── 1
   ╰────
"""
    assert str(rust_error.value) == expected


def test_render_url_invalid_keyword(assert_parse_error):
    template = "{% url foo= %}"
    django_message = snapshot("Could not parse the remainder: '=' from 'foo='")
    rusty_message = snapshot("""\
  × Incomplete keyword argument
   ╭────
 1 │ {% url foo= %}
   ·        ──┬─
   ·          ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_url_invalid_dotted_lookup_keyword(assert_parse_error):
    template = "{% url foo.bar= %}"
    django_message = snapshot("Could not parse the remainder: '=' from 'foo.bar='")
    rusty_message = snapshot("""\
  × Could not parse the remainder
   ╭────
 1 │ {% url foo.bar= %}
   ·               ┬
   ·               ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_url_dotted_lookup_keyword(assert_parse_error):
    template = "{% url foo.bar='lily' %}"
    django_message = snapshot(
        "Could not parse the remainder: '='lily'' from 'foo.bar='lily''"
    )
    rusty_message = snapshot("""\
  × Could not parse the remainder
   ╭────
 1 │ {% url foo.bar='lily' %}
   ·               ───┬───
   ·                  ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_render_url_variable_missing(assert_render_error):
    assert_render_error(
        template="{% url home %}",
        context={},
        exception=NoReverseMatch,
        django_message=snapshot(
            "Reverse for '' not found. '' is not a valid view function or pattern name."
        ),
        rusty_message=snapshot(
            """\
  × Reverse for '' not found. '' is not a valid view function or pattern name.
   ╭────
 1 │ {% url home %}
   · ───────┬──────
   ·        ╰── here
   ╰────
"""
        ),
    )


def test_render_url_dotted_lookup_filter_with_equal_char(assert_render_error):
    template = "{% url foo.bar|default:'=' %}"

    django_message = snapshot(
        "Reverse for '=' not found. '=' is not a valid view function or pattern name."
    )
    rusty_message = snapshot(
        """\
  × Reverse for '=' not found. '=' is not a valid view function or pattern
  │ name.
   ╭────
 1 │ {% url foo.bar|default:'=' %}
   · ──────────────┬──────────────
   ·               ╰── here
   ╰────
"""
    )

    assert_render_error(
        template=template,
        context={},
        exception=NoReverseMatch,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_render_url_missing_extra_kwarg(assert_render_error):
    template = "{% url 'users:user' username='Lily' other=missing %}"
    request = factory.get("/")

    django_message = snapshot(
        "Reverse for 'user' with keyword arguments '{'username': 'Lily', 'other': ''}' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']"
    )
    rusty_message = snapshot(
        """\
  × Reverse for 'user' with keyword arguments '{'username': 'Lily', 'other':
  │ None}' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']
   ╭────
 1 │ {% url 'users:user' username='Lily' other=missing %}
   · ──────────────────────────┬─────────────────────────
   ·                           ╰── here
   ╰────
"""
    )
    assert_render_error(
        template=template,
        context={},
        exception=NoReverseMatch,
        django_message=django_message,
        rusty_message=rusty_message,
        request_factory=request,
    )


def test_render_url_var_after_as(assert_render_error):
    template = "{% url 'users:user' as my_url my_url my_url %}"
    request = factory.get("/")

    django_message = snapshot(
        "Reverse for 'user' with arguments '('', '', '', '')' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']"
    )
    rusty_message = snapshot(
        """\
  × Reverse for 'user' with arguments '('', '', '', '')' not found. 1
  │ pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']
   ╭────
 1 │ {% url 'users:user' as my_url my_url my_url %}
   · ───────────────────────┬──────────────────────
   ·                        ╰── here
   ╰────
"""
    )
    assert_render_error(
        template=template,
        context={},
        exception=NoReverseMatch,
        django_message=django_message,
        rusty_message=rusty_message,
        request_factory=request,
    )


def test_render_valid_url_and_invalid_as_binding(assert_render_error):
    template = "{% url 'users:user' 'lily' as my_url my_url %}"
    request = factory.get("/")

    django_message = snapshot(
        "Reverse for 'user' with arguments '('lily', '', '', '')' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']"
    )
    rusty_message = snapshot(
        """\
  × Reverse for 'user' with arguments '('lily', '', '', '')' not found. 1
  │ pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']
   ╭────
 1 │ {% url 'users:user' 'lily' as my_url my_url %}
   · ───────────────────────┬──────────────────────
   ·                        ╰── here
   ╰────
"""
    )
    assert_render_error(
        template=template,
        context={},
        exception=NoReverseMatch,
        django_message=django_message,
        rusty_message=rusty_message,
        request_factory=request,
    )
