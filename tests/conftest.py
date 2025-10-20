import pytest
from django.template import engines, TemplateSyntaxError


@pytest.fixture(params=["rusty", "django"])
def template_engine(request):
    """
    Parametrize tests to run against both rusty and django template engines.

    See https://docs.pytest.org/en/stable/how-to/fixtures.html#parametrizing-fixtures
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


@pytest.fixture(params=["rusty", "django"])
def assert_parse_error(request):
    """
    A convenient method to test `TemplateSyntaxError` for both engines.

    Example:
        def test_error(assert_parse_error):
            assert_parse_error(
                template=...,
                django_message="invalid literal for int() with base 10: '-5.5'",
                rusty_message="  × Couldn't convert argument (-5.5) to integer..."
            )

    """

    def _assert_parse_error(template, django_message, rusty_message):
        message = django_message if request.param == "django" else rusty_message
        with pytest.raises(TemplateSyntaxError) as exc_info:
            engines[request.param].from_string(template)
        assert str(exc_info.value) == message

    return _assert_parse_error
