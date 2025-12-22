"""
Adapted from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_length.py
"""

import pytest
from django.utils.safestring import mark_safe


@pytest.mark.parametrize(
    'template,context,expected',
    [
        pytest.param(
            '{{ list|length }}',
            {"list": ["4", None, True, {}]},
            "4",
            id='test_length_01',
        ),
        pytest.param(
            '{{ list|length }}',
            {"list": []},
            "0",
            id='test_length_02',
        ),
        pytest.param(
            '{{ string|length }}',
            {"string": ""},
            "0",
            id='test_length_03',
        ),
        pytest.param(
            '{{ string|length }}',
            {"string": "django"},
            "6",
            id='test_length_04',
        ),
        pytest.param(
            '{% if string|length == 6 %}Pass{% endif %}',
            {"string": mark_safe("django")},
            "Pass",
            id='test_length_05',
        ),
        pytest.param(
            '{{ int|length }}',
            {"int": 7},
            "0",
            id='test_length_06',
        ),
        pytest.param(
            '{{ None|length }}',
            {"None": None},
            "0",
            id='test_length_07',
        ),
    ]
)
def test_length(assert_render, template, context, expected):
    assert_render(template, context, expected)