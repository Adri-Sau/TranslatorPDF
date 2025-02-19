import func
import click


@click.group()
def base():
    pass

base.add_command(func.print)

if __name__ == "__main__":
    base()
