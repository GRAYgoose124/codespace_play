import importlib
import json
import click


@click.group()
def cli():
    pass


def load_commands():
    with open("commands.json") as f:
        commands = json.load(f)

    for command_name, command_path in commands.items():
        module_path, function_name = command_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        command = getattr(module, function_name)
        cli.add_command(command, name=command_name)


def main():
    load_commands()
    cli()


if __name__ == "__main__":
    main()
