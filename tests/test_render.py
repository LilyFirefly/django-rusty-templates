import pytest
from django.shortcuts import render
from django.template import Context, RequestContext
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.test import RequestFactory


class TestUserFacingTemplateRenderSuccess:
    """
    Test that the user-facing rendering entrypoints work correctly with dict contexts.
    """

    def test_render_shortcut_with_dict(self, template_engine):
        """
        `render()` shortcut function

        See https://docs.djangoproject.com/en/stable/topics/http/shortcuts/#render
        """
        request = RequestFactory().get("/")
        template = "basic.txt"
        context = {"user": "Lily"}

        response = render(request, template, context, using=template_engine.name)
        assert response.status_code == 200
        assert response.content == b"Hello Lily!\n"

    def test_template_response_rendered_content(self, template_engine):
        """
        `TemplateResponse` -- a "lazy" way to render a template with a request context

        This is used in django.views.generic.TemplateView

        See https://docs.djangoproject.com/en/stable/ref/template-response/#templateresponse-objects
        """
        if template_engine.name == "rusty":
            pytest.skip("Rusty engine need to support context processor first")

        request = RequestFactory().get("/")
        template = template_engine.from_string(
            "{{ request.path }} {{ request.method }} -> {{ foo }}"
        )
        context = {"foo": "bar"}

        response = TemplateResponse(request, template, context)
        response.render()

        assert response.is_rendered
        assert response.rendered_content == "GET / -> bar"

    def test_simple_template_response_rendered_content(self, template_engine):
        """
        `SimpleTemplateResponse` -- a "lazy" way to render a template

        See https://docs.djangoproject.com/en/stable/ref/template-response/#simpletemplateresponse-objects
        """
        template = template_engine.from_string("{{ foo }}")
        context = {"foo": "bar"}

        response = SimpleTemplateResponse(template, context)
        response.render()

        assert response.is_rendered
        assert response.rendered_content == "bar"


class TestUserFacingTemplateRenderRequiresDict:
    """
    Django user facing rendering entrypoints expect only a dict and will internally
    build a proper Context object in `django.template.context.make_context`.
    Attempts to pass a `Context` or `RequestContext` directly should cause errors.

    See https://github.com/django/django/blob/340e4f832e1ea74a27770e38635bbc781979f2e0/django/template/context.py#L290C5-L290C17
    """

    def test_render_shortcut_requires_dict(self, template_engine):
        if template_engine.name == "rusty":
            pytest.skip(
                "Rusty engine currently fails with `argument 'context': 'Context' object cannot be cast as 'dict'`"
                "We should refine the error to match django"
            )

        template = "basic.txt"
        request = RequestFactory().get("/")
        context = Context({"foo": "bar"})

        with pytest.raises(
            TypeError, match="context must be a dict rather than Context"
        ):
            render(request, template, context, using=template_engine.name)

        request_context = RequestContext(request, {"foo": "bar"})
        with pytest.raises(
            TypeError, match="context must be a dict rather than RequestContext"
        ):
            render(request, template, request_context, using=template_engine.name)

    def test_template_render_requires_dict(self, template_engine):
        if template_engine.name == "rusty":
            pytest.skip(
                "Rusty engine currently fails with `argument 'context': 'Context' object cannot be cast as 'dict'`"
                "We should refine the error to match django"
            )

        template = template_engine.from_string("{{ foo }}")
        context = Context({"foo": "bar"})
        with pytest.raises(
            TypeError, match="context must be a dict rather than Context"
        ):
            template.render(context)

        request_context = RequestContext(RequestFactory().get("/"), {"foo": "bar"})
        with pytest.raises(
            TypeError, match="context must be a dict rather than RequestContext"
        ):
            template.render(request_context)

    def test_simple_template_response_requires_dict(self, template_engine):
        if template_engine.name == "rusty":
            pytest.skip(
                "Rusty engine currently fails with `argument 'context': 'Context' object cannot be cast as 'dict'`"
                "We should refine the error to match django"
            )

        template = template_engine.from_string("{{ foo }}")
        context = Context({"foo": "bar"})

        response = SimpleTemplateResponse(template, context)
        with pytest.raises(
            TypeError, match="context must be a dict rather than Context"
        ):
            response.render()

        request_context = RequestContext(RequestFactory().get("/"), {"foo": "bar"})
        response = SimpleTemplateResponse(template, request_context)
        with pytest.raises(
            TypeError, match="context must be a dict rather than RequestContext"
        ):
            response.render()

    def test_template_response_requires_dict(self, template_engine):
        if template_engine.name == "rusty":
            pytest.skip(
                "Rusty engine currently fails with `argument 'context': 'Context' object cannot be cast as 'dict'`"
                "We should refine the error to match django"
            )

        request = RequestFactory().get("/")
        template = template_engine.from_string("{{ foo }}")
        context = Context({"foo": "bar"})

        response = TemplateResponse(request, template, context)
        with pytest.raises(
            TypeError, match="context must be a dict rather than Context"
        ):
            response.render()

        request_context = RequestContext(request, {"foo": "bar"})
        response = TemplateResponse(request, template, request_context)
        with pytest.raises(
            TypeError, match="context must be a dict rather than RequestContext"
        ):
            response.render()
