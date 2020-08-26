import click

def test_matcher_factory(test_runner):
    """
        Return matcher for named test_runner
    """
    if test_runner == 'unity':
        return UnityMatcher
    if test_runner is None or test_runner == 'none':
        return EmptyMatcher

    raise ValueError(f'Unknown test matcher {test_runner}')

def echo_line(line, color):
    """
        Try to echo a line with color, otherwise just emit it raw
    """
    try:
        decoded_line = line.decode()
        click.secho(decoded_line, fg=color)
    except UnicodeDecodeError:
        click.echo(line)

class UnityMatcher:
    summary_separator = b'-----------------------'

    def __init__(self, io):
        self.state = b''
        self.separator = None
        self.has_fail = False
        self.in_summary = False
        self.io = io

    def feed(self, data):
        self.state += data
        if b'\n' not in data:
            return

        lines = self.state.split(b'\n')
        to_process, remainder = lines[:-1], lines[-1]
        self.state = remainder
        for line in to_process:
            if line == self.summary_separator:
                self.in_summary = True
                click.echo(line)
                continue
            if self.in_summary:
                color = 'red' if self.has_fail else 'green'
                echo_line(line, color)
            else:
                if b':FAIL' in line:
                    self.has_fail = True
                    echo_line(line, 'red')
                elif b':PASS' in line:
                    echo_line(line, 'green')
                elif b':INFO' in line:
                    echo_line(line, 'yellow')
                else:
                    click.echo(line)

    def done(self):
        pass

    @property
    def exit_code(self):
        if self.has_fail:
            return 1
        return 0

class EmptyMatcher:
    def __init__(self, io):
        self.io = io

    def feed(self, data):
        self.io.output(data)

    def done(self):
        pass

    @property
    def exit_code(self):
        return 0
