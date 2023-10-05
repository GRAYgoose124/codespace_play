import click


@click.command()
def command1():
    click.echo("Running Command 1!")


@click.command()
def command2():
    click.echo("Running Command 2!")
