import click

@click.command()
@click.argument('name')
@click.option('-e', type=bool, is_flag=True)
def print(name: str, e: bool) -> None:
    if e:
        click.echo(f'Hello, {name}!')
    else:
        click.echo(f'Hello, {name}.')