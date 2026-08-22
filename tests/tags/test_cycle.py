def test_cycle_literals_in_loop(assert_render):
    template = '{% for item in items %}{% cycle "odd" "even" %}{% endfor %}'
    context = {"items": range(4)}
    expected = "oddevenoddeven"

    assert_render(
        template=template,
        context=context,
        expected=expected,
    )
