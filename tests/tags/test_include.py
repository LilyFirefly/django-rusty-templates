def test_include(assert_render):
    template = "{% for user in users %}{% include 'basic.txt' %}{% endfor %}"
    users = ["Lily", "Jacob", "Bryony"]
    expected = "Hello Lily!\nHello Jacob!\nHello Bryony!\n"
    assert_render(template=template, context={"users": users}, expected=expected)
