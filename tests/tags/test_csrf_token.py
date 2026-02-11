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


def test_csrf_token_basic(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": "test123"},
        expected='<input type="hidden" name="csrfmiddlewaretoken" value="test123">',
    )


def test_csrf_token_not_provided(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": "NOTPROVIDED"},
        expected="",
    )


def test_csrf_token_missing(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={},
        expected="",
    )


def test_csrf_token_escaping(render_output):
    result = render_output(
        template="{% csrf_token %}",
        context={"csrf_token": 'test"with<quotes>&amp;'},
    )
    assert 'value="test&quot;with&lt;quotes&gt;&amp;amp;"' in result


def test_csrf_token_empty_string(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": ""},
        expected="",
    )


def test_csrf_token_none_value(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": None},
        expected="",
    )


def test_csrf_token_numeric_value(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": 12345},
        expected='<input type="hidden" name="csrfmiddlewaretoken" value="12345">',
    )


def test_csrf_token_zero_value(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": 0},
        expected="",
    )


def test_csrf_token_false_value(assert_render):
    assert_render(
        template="{% csrf_token %}",
        context={"csrf_token": False},
        expected="",
    )


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
