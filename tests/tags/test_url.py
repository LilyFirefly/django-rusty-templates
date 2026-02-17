from inline_snapshot import snapshot
import pytest
from django.template import engines
from django.template.base import VariableDoesNotExist
from django.test import RequestFactory
from django.urls import resolve, NoReverseMatch


factory = RequestFactory()


def test_render_url(assert_render):
    template = "{% url 'home' %}"
    expected = "/"
    assert_render(template, {}, expected)


def test_render_url_variable(assert_render):
    assert_render(template="{% url home %}", context={"home": "home"}, expected="/")


def test_render_url_variable_missing(template_engine):
    template = "{% url home %}"
    template = template_engine.from_string(template)

    with pytest.raises(NoReverseMatch) as exc_info:
        template.render({})

    msg = "Reverse for '' not found. '' is not a valid view function or pattern name."
    assert str(exc_info.value) == msg


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


def test_render_url_dotted_lookup_filter_with_equal_char(template_engine):
    template = "{% url foo.bar|default:'=' %}"
    template_obj = template_engine.from_string(template)

    with pytest.raises(NoReverseMatch) as exc_info:
        template_obj.render({})

    msg = "Reverse for '=' not found. '=' is not a valid view function or pattern name."
    assert str(exc_info.value) == msg


def test_render_url_var_after_as(assert_render_error):
    template = "{% url 'users:user' as my_url my_url my_url %}"
    request = factory.get("/")

    django_message = snapshot(
        "Reverse for 'user' with arguments '('', '', '', '')' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']"
    )
    rusty_message = snapshot(
        "Reverse for 'user' with arguments '('', '', '', '')' not found. 1 pattern(s) tried: ['users/(?P<username>[^/]+)/\\\\Z']"
    )
    assert_render_error(
        template=template,
        context={},
        exception=NoReverseMatch,
        django_message=django_message,
        rusty_message=rusty_message,
        request_factory=request,
    )
