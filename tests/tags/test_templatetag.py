from inline_snapshot import snapshot


def test_templatetag_openblock(assert_render):
    assert_render(
        template="{% templatetag openblock %}",
        context={},
        expected="{%",
    )


def test_templatetag_closeblock(assert_render):
    assert_render(
        template="{% templatetag closeblock %}",
        context={},
        expected="%}",
    )


def test_templatetag_openvariable(assert_render):
    assert_render(
        template="{% templatetag openvariable %}",
        context={},
        expected="{{",
    )


def test_templatetag_closevariable(assert_render):
    assert_render(
        template="{% templatetag closevariable %}",
        context={},
        expected="}}",
    )


def test_templatetag_openbrace(assert_render):
    assert_render(
        template="{% templatetag openbrace %}",
        context={},
        expected="{",
    )


def test_templatetag_closebrace(assert_render):
    assert_render(
        template="{% templatetag closebrace %}",
        context={},
        expected="}",
    )


def test_templatetag_opencomment(assert_render):
    assert_render(
        template="{% templatetag opencomment %}",
        context={},
        expected="{#",
    )


def test_templatetag_closecomment(assert_render):
    assert_render(
        template="{% templatetag closecomment %}",
        context={},
        expected="#}",
    )


def test_templatetag_combined(assert_render):
    assert_render(
        template="{% templatetag openblock %} templatetag openblock {% templatetag closeblock %}",
        context={},
        expected="{% templatetag openblock %}",
    )


def test_templatetag_no_args(assert_parse_error):
    assert_parse_error(
        template="{% templatetag %}",
        django_message=snapshot("'templatetag' statement takes one argument"),
        rusty_message=snapshot("""\
  × 'templatetag' statement takes one argument
   ╭────
 1 │ {% templatetag %}
   ·               ▲
   ·               ╰── missing argument
   ╰────
"""),
    )


def test_templatetag_invalid_argument(assert_parse_error):
    assert_parse_error(
        template="{% templatetag invalid %}",
        django_message=snapshot(
            "Invalid templatetag argument: 'invalid'. Must be one of: ['openblock', 'closeblock', 'openvariable', 'closevariable', 'openbrace', 'closebrace', 'opencomment', 'closecomment']"
        ),
        rusty_message=snapshot("""\
  × Invalid templatetag argument: 'invalid'
   ╭────
 1 │ {% templatetag invalid %}
   ·                ───┬───
   ·                   ╰── invalid argument
   ╰────
  help: Must be one of: openblock, closeblock, openvariable, closevariable,
        openbrace, closebrace, opencomment, closecomment
"""),
    )


def test_templatetag_too_many_args(assert_parse_error):
    assert_parse_error(
        template="{% templatetag openblock extra %}",
        django_message=snapshot("'templatetag' statement takes one argument"),
        rusty_message=snapshot("""\
  × 'templatetag' statement takes one argument
   ╭────
 1 │ {% templatetag openblock extra %}
   ·                          ──┬──
   ·                            ╰── extra argument
   ╰────
"""),
    )
