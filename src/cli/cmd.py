import click
import translator

@click.command()
@click.argument('filepath', type=str, required=True)
@click.option('-p', is_flag=True)
def translate(filepath: str, p: bool = False) -> None:
    try:
        translator.Translate(filepath, p)
    except Exception as e:
        click.echo(f"Error: {e}")
