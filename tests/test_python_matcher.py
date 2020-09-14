from lager_cli.matchers import PythonMatcherV1

def test_matcher():
    separator = b'foo'
    matcher = PythonMatcherV1(separator)
    matcher.feed(b'abc\n')
    matcher.feed(b'\nfoo\n')
    matcher.feed(b'0')
    assert matcher.exit_code == 0

    matcher = PythonMatcherV1(separator)
    matcher.feed(b'abc\n')
    matcher.feed(b'\nfoo\n')
    matcher.feed(b'42')
    assert matcher.exit_code == 42
