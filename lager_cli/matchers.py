import click

def test_matcher_factory(test_runner):
    if test_runner == 'unity':
        return UnityMatcher
    return EmptyMatcher

class UnityMatcher:
    summary_separator = '-----------------------'

    def __init__(self):
        self.state = ''
        self.separator = None
        self.has_fail = False
        self.in_summary = False

    def feed(self, data):
        self.state += data
        if '\n' not in data:
            return

        lines = self.state.split('\n')
        to_process, remainder = lines[:-1], lines[-1]
        self.state = remainder
        for line in to_process:
            if line == self.summary_separator:
                self.in_summary = True
                click.echo(line)
                continue
            if self.in_summary:
                color = 'red' if self.has_fail else 'green'
                click.secho(line, fg=color)
            else:
                if ':FAIL' in line:
                    self.has_fail = True
                    click.secho(line, fg='red')
                elif ':PASS' in line:
                    click.secho(line, fg='green')
                elif ':INFO' in line:
                    click.secho(line, fg='yellow')
                else:
                    click.echo(line)

        # click.echo(data, nl=False)

    def done(self):
        pass

    @property
    def exit_code(self):
        if self.has_fail:
            return 1
        return 0

class EmptyMatcher:
    def __init__(self):
        pass

    def feed(self, data):
        click.echo(data, nl=False)

    def done(self):
        pass

    @property
    def exit_code(self):
        return 0
