import warnings
from django.template import engines
from django.test import override_settings


def test_csrf_token_basic():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": "test123"}
    expected = '<input type="hidden" name="csrfmiddlewaretoken" value="test123">'

    assert django_template.render(context) == expected
    assert rust_template.render(context) == expected


def test_csrf_token_not_provided():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": "NOTPROVIDED"}

    assert django_template.render(context) == ""
    assert rust_template.render(context) == ""


def test_csrf_token_missing():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == ""
    assert rust_template.render({}) == ""


def test_csrf_token_escaping():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": 'test"with<quotes>&amp;'}

    django_result = django_template.render(context)
    rust_result = rust_template.render(context)

    assert django_result == rust_result
    assert 'value="test&quot;with&lt;quotes&gt;&amp;amp;"' in rust_result


def test_csrf_token_empty_string():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": ""}

    assert django_template.render(context) == ""
    assert rust_template.render(context) == ""


def test_csrf_token_none_value():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": None}

    assert django_template.render(context) == ""
    assert rust_template.render(context) == ""


def test_csrf_token_numeric_value():
    template = "{% csrf_token %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": 12345}
    expected = '<input type="hidden" name="csrfmiddlewaretoken" value="12345">'

    assert django_template.render(context) == expected
    assert rust_template.render(context) == expected


def test_csrf_token_zero_value():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": 0}

    assert django_template.render(context) == ""
    assert rust_template.render(context) == ""


def test_csrf_token_false_value():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"csrf_token": False}

    assert django_template.render(context) == ""
    assert rust_template.render(context) == ""


@override_settings(DEBUG=True)
def test_csrf_token_missing_debug_warning():
    template = "{% csrf_token %}"

    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    expected = "A {% csrf_token %} was used in a template, but the context did not provide the value.  This is usually caused by not using RequestContext."

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert django_template.render({}) == ""
        assert str(w[0].message) == expected

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert rust_template.render({}) == ""
        assert str(w[0].message) == expected
