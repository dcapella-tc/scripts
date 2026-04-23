"""Tests for html_to_dict.html_string_to_dict."""

from html_to_dict import html_string_to_dict


def test_simple_paragraph():
    result = html_string_to_dict('<p>a</p>')
    assert result == {
        'tag': 'p',
        'attrs': {},
        'children': ['a'],
    }


def test_nested_divs():
    result = html_string_to_dict('<div><div><span>x</span></div></div>')
    assert result['tag'] == 'div'
    inner = result['children'][0]
    assert inner['tag'] == 'div'
    span = inner['children'][0]
    assert span == {'tag': 'span', 'attrs': {}, 'children': ['x']}


def test_class_attribute_list():
    result = html_string_to_dict('<p class="a b">t</p>')
    assert result['attrs']['class'] == ['a', 'b']


def test_void_br():
    result = html_string_to_dict('<div>a<br/>b</div>')
    assert result['children'][0] == 'a'
    br = result['children'][1]
    assert br == {'tag': 'br', 'attrs': {}, 'children': []}
    assert result['children'][2] == 'b'


def test_fragment_multiple_roots():
    result = html_string_to_dict('<p>one</p><p>two</p>')
    assert result['tag'] == '_fragment_'
    assert result['attrs'] == {}
    assert len(result['children']) == 2
    assert result['children'][0]['children'] == ['one']
    assert result['children'][1]['children'] == ['two']


def test_full_document_single_html_root():
    html = '<!DOCTYPE html><html><head></head><body>z</body></html>'
    result = html_string_to_dict(html)
    assert result['tag'] == 'html'
    assert any(c.get('tag') == 'body' for c in result['children'] if isinstance(c, dict))


def test_utf8_text():
    result = html_string_to_dict('<p>Café 日本</p>')
    assert result['children'] == ['Café 日本']


def test_whitespace_collapsed_on_text_nodes():
    result = html_string_to_dict('<p>  hi  </p>')
    assert result['children'] == ['hi']


def test_comments_omitted():
    result = html_string_to_dict('<p><!-- x -->y</p>')
    assert result['children'] == ['y']


def test_empty_input_fragment():
    result = html_string_to_dict('')
    assert result == {'tag': '_fragment_', 'attrs': {}, 'children': []}
