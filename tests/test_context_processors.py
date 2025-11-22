import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory


@pytest.mark.parametrize("user", (None, "Lily"))
def test_auth_context_processor(assert_render, user):
    request = RequestFactory().get("/")
    if user:
        request.user = User(username=user)
        expected = user
    else:
        expected = ""

    assert_render("{{ user.username }}", {}, expected, request=request)
