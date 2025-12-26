import pytest
from django.template import engines, TemplateSyntaxError

all_engines = pytest.fixture(params=["rusty", "django"])
all_engines_nocache = pytest.fixture(params=["rusty_nocache", "django_nocache"])


@all_engines
def template_engine(request):
    """
    Parametrize tests to run against both rusty and django template engines.

    See https://docs.pytest.org/en/stable/how-to/fixtures.html#parametrizing-fixtures
    """
    return engines[request.param]


@all_engines_nocache
def template_engine_nocache(request):
    """
    Like template_engine, but forces usage of the filesystem loader without the cached loader.
    """
    return engines[request.param]


@pytest.fixture
def assert_render(template_engine):
    """
    A convenient method allowing to write concise tests rendering a template with a specific context.

    Example:
        def test_render_url_variable(assert_render):
            assert_render(template="{% url home %}", context={"home": "home"}, expected="/")
    """

    def assert_render_template(template, context, expected, request=None):
        template = template_engine.from_string(template)
        assert template.render(context, request) == expected

    return assert_render_template


@pytest.fixture
def render_output(template_engine):
    def render_template_output(template, context, request=None):
        template = template_engine.from_string(template)
        return template.render(context, request)

    return render_template_output


@all_engines
def assert_parse_error(request):
    """
    A convenient method to test `TemplateSyntaxError` for both engines.

    Example:
        def test_error(assert_parse_error):
            assert_parse_error(
                template=...,
                django_message = snapshot("invalid literal for int() with base 10: '-5.5'"),
                rusty_message = snapshot("  × Couldn't convert argument (-5.5) to integer...")
            )

    """

    def _assert_parse_error(
        template,
        django_message,
        rusty_message,
        exception=TemplateSyntaxError,
        rusty_exception=None,
    ):
        message = django_message if request.param == "django" else rusty_message
        exception = (
            rusty_exception
            if request.param != "django" and rusty_exception
            else exception
        )
        with pytest.raises(exception) as exc_info:
            engines[request.param].from_string(template)
        assert str(exc_info.value) == message

    return _assert_parse_error


@all_engines
def assert_render_error(request):
    """
    A convenient method to test rendering exception with both engines.

    Example:
        def test_error(assert_render_error):
            assert_render_error(
                template="{{ foo|center:bar }}",
                context={"foo": "test", "bar": "-5.5"},
                exception=ValueError,
                django_message = snapshot("invalid literal for int() with base 10: '-5.5'"),
                rusty_message = snapshot("  × Couldn't convert argument (-5.5) to integer...")
            )
    """

    def _assert_render_error(
        template,
        context,
        exception,
        django_message,
        rusty_message,
        rusty_exception=None,
    ):
        message = django_message if request.param == "django" else rusty_message
        exception = (
            rusty_exception
            if request.param != "django" and rusty_exception
            else exception
        )
        template = engines[request.param].from_string(template)
        with pytest.raises(exception) as exc_info:
            template.render(context)
        assert str(exc_info.value) == message

    return _assert_render_error
