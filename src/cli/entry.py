import cli.cmd as cmd
import click


@click.group()
def main(): # code that runs every time a command is run
    pass

main.add_command(cmd.translate)

if __name__ == "__main__":
    main()
