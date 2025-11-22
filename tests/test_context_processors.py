import pytest
from django.contrib.auth.models import User
from django.template.backends.django import DjangoTemplates
from django.test import RequestFactory

from django_rusty_templates import RustyTemplates


@pytest.mark.parametrize("user", (None, "Lily"))
def test_auth_context_processor(assert_render, user):
    request = RequestFactory().get("/")
    if user:
        request.user = User(username=user)
        expected = user
    else:
        expected = ""

    assert_render("{{ user.username }}", {}, expected, request=request)


@pytest.mark.parametrize("engine_class", (RustyTemplates, DjangoTemplates))
def test_missing_context_processor(engine_class):
    params = {
        "APP_DIRS": False,
        "DIRS": [],
        "NAME": "test",
        "OPTIONS": {
            "context_processors": ["invalid.processor"],
        },
    }
    request = RequestFactory().get("/")

    # RustyTemplates imports context processors when created.
    # DjangoTemplates keeps them as strings until the first template render
    # which calls `Engine.template_context_processors`. This is thereafter
    # cached on the `Engine` instance.
    # I don't think we need to delay this in RustyTemplates, so I'm happy to
    # live with this discrepancy.
    # https://github.com/django/django/blob/ec60df6d1ea8939a316d9b180faa0b4ef2e83606/django/template/engine.py#L115
    # https://github.com/django/django/blob/ec60df6d1ea8939a316d9b180faa0b4ef2e83606/django/template/context.py#L260
    # https://github.com/django/django/blob/ec60df6d1ea8939a316d9b180faa0b4ef2e83606/django/template/base.py#L171
    with pytest.raises(ModuleNotFoundError) as exc_info:
        engine = engine_class(params)  # RustyTemplates raises here
        template = engine.from_string("")
        template.render({}, request)  # DjangoTemplates raises here

    assert str(exc_info.value) == "No module named 'invalid'"


def broken(request):
    1 / 0


@pytest.mark.parametrize("engine_class", (RustyTemplates, DjangoTemplates))
def test_broken_context_processor(engine_class):
    params = {
        "APP_DIRS": False,
        "DIRS": [],
        "NAME": "test",
        "OPTIONS": {
            "context_processors": ["tests.test_context_processors.broken"],
        },
    }
    engine = engine_class(params)
    template = engine.from_string("")
    request = RequestFactory().get("/")

    with pytest.raises(ZeroDivisionError):
        template.render({}, request)
