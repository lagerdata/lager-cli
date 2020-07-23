import click

def test_matcher_factory(test_runner):
    if test_runner == 'unity':
        return UnityMatcher
    return EmptyMatcher

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

    def __init__(self, stdscr):
        self.state = b''
        self.separator = None
        self.has_fail = False
        self.in_summary = False
        self.stdscr = stdscr

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
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def feed(self, data):
        self.stdscr.addstr(data)
        self.stdscr.refresh()
        # click.echo(data, nl=False)

    def done(self):
        pass

    @property
    def exit_code(self):
        return 0
