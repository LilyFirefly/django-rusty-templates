import re
import warnings

import pytest
from django.template import engines
from django.template.backends.django import DjangoTemplates
from django.test import RequestFactory, override_settings

from django_rusty_templates import RustyTemplates


factory = RequestFactory()


@pytest.mark.parametrize("engine_class", (RustyTemplates, DjangoTemplates))
def test_csrf_token_context_processor(engine_class):
    template = "{% csrf_token %}"
    request = factory.get("/")

    params = {
        "APP_DIRS": False,
        "DIRS": [],
        "NAME": "test",
        "OPTIONS": {
            "context_processors": ["django.template.context_processors.csrf"],
        },
    }

    engine = engine_class(params)
    rendered = engine.from_string(template).render({}, request)

    assert (
        re.fullmatch(
            r'^<input type="hidden" name="csrfmiddlewaretoken" value="([a-zA-Z0-9]{64})">$',
            rendered,
        )
        is not None
    )


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

    django_expected = "A {% csrf_token %} was used in a template, but the context did not provide the value.  This is usually caused by not using RequestContext."
    rusty_expected = "A {% csrf_token %} was used in a template, but the context did not provide the value.  This is usually caused by not providing a request."

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert django_template.render({}) == ""
        assert str(w[0].message) == django_expected

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert rust_template.render({}) == ""
        assert str(w[0].message) == rusty_expected
