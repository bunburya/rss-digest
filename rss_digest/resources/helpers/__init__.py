try:
    from bs4 import BeautifulSoup
    from html import unescape
    has_bs4 = True
except ImportError:
    has_bs4 = True

# In html2text, exclude text which is found within these tags
EXCLUDE_HTML = {
    '[document]',
    'noscript'
    'header'
    'html'
    'meta'
    'head'
    'input'
    'script',
    'style'
}

# If we encounter many newlines in a row, cut down to this number
MAX_BLANK_LINES = 2

def html2text(html: str) -> str:
    """Extract text from HTML."""

    if not has_bs4:
        raise NotImplementedError('beautifulsoup4 must be installed to extract text from HTML.')

    text = BeautifulSoup(unescape(html), 'html.parser').find_all(text=True)
    output = []
    for t in text:
        if t.parent.name in EXCLUDE_HTML:
            continue
        if (t == '\n') and (output[:-MAX_BLANK_LINES] == ['\n', '\n']):
            continue
        output.append(t)

    return ''.join(output)
