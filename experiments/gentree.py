import ast
import inspect
import dis
import io
from pathlib import Path
import re
import sys
from typing import Any
from contextlib import contextmanager


@contextmanager
def captured_stdout():
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = original_stdout


class CommandError(Exception):
    pass


class CliModuleMeta(type):
    def __init__(cls, name, bases, clsdict):
        for attr_name, maybe_climod in clsdict.items():
            if isinstance(maybe_climod, type) and issubclass(maybe_climod, CliModule):
                instance = maybe_climod()
                setattr(cls, attr_name, instance)

        super().__init__(name, bases, clsdict)


class CliModule(metaclass=CliModuleMeta):
    """Nestable cli module."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

        self.commands = {}
        self.submodules = {}

        for name, attribute in inspect.getmembers(self):
            if isinstance(attribute, CliModule):
                if name == "_":
                    self.commands.update(attribute.commands)
                else:
                    self.submodules[attribute.__class__.__name__] = attribute

        self.commands.update(
            {
                name: func
                for name, func in inspect.getmembers(self, callable)
                if name == "help"
                or name not in CliModule.__dict__
                and not name.startswith("_")
            }
        )

    def process(self, user_input: str, raw_input=None) -> Any:
        if self.prefix:
            if not user_input.startswith(self.prefix):
                return
            user_input = user_input[len(self.prefix) :]

        try:
            command, *args = user_input.split()
        except ValueError:
            raise CommandError(f"{self.__class__.__name__}:no command given")

        if command in self.commands:
            try:
                if raw_input:
                    args = [raw_input] + args
                return self.commands[command](*args)
            except TypeError as e:
                ex = str(e).split(" ", maxsplit=1)[-1]
                raise CommandError(f"{self.__class__.__name__}:{command} is {ex}")
            except Exception as e:
                raise CommandError(f"{self.__class__.__name__}:{command} raised {e}")
        elif command in self.submodules:
            try:
                return self.submodules[command].process(
                    user_input[len(command) + 1 :], raw_input=raw_input
                )
            except CommandError as e:
                raise CommandError(f"{self.__class__.__name__}:{e}")
        else:
            raise CommandError(f"{self.__class__.__name__}:{command} is unknown")

    def help(self, command: str = "") -> None:
        """Print help for a command."""
        if command == "":
            print(f"Help for {self.__class__.__name__}:")
            print("Commands: <command> <args>")
            for name, command in self.commands.items():
                print(f"\t{name}")

            if self.submodules:
                print("Submodules: <sub> [<sub2> ...] <command> <args>")
                for name, submodule in self.submodules.items():
                    print(f"\t{name}")

        if command in self.commands:
            print(self.commands[command].__doc__)
        else:
            for name, submodule in self.submodules.items():
                submodule.help(command)


class Pipeline:
    def __init__(self, cli_module: CliModule):
        self.cli_module = cli_module

    def _parse_command_chain(self, command_chain: str):
        parts = re.split("([|$])", command_chain)

        commands = [
            (parts[i + 1], parts[i + 2].strip()) for i in range(0, len(parts) - 2, 2)
        ]

        commands.insert(0, (None, parts[0].strip()))

        return commands

    def execute(self, command_chain: str, last_return_value=None) -> Any:
        final = None
        with captured_stdout() as captured:
            raw_input = last_return_value
            for operator, command in self._parse_command_chain(command_chain):
                if operator == "$":
                    raw_input = last_return_value
                elif operator == "|":
                    raw_input = captured.getvalue()
                    captured.truncate(0)

                last_return_value = self.cli_module.process(
                    command.strip(), raw_input=raw_input
                )

            if captured.getvalue():
                final = captured.getvalue().strip()

        if final:
            print(final, end="")

        return last_return_value


class CliApp:
    @staticmethod
    def Root() -> CliModule:
        raise NotImplementedError

    def __init__(self) -> None:
        self.root: CliModule = self.Root()
        self.pipeline = Pipeline(self.root)

    def run(self):
        result = None
        while True:
            try:
                user_input = input(": ")
                result = self.pipeline.execute(user_input, last_return_value=result)
            except KeyboardInterrupt:
                print()
            except SystemExit:
                break
            except CommandError as e:
                print(f"{e}")


class AstExplorer(CliApp):
    class Root(CliModule):
        class ast(CliModule):
            class p(CliModule):
                @staticmethod
                def parse(source: str) -> str:
                    """Parse a file."""
                    return ast.dump(ast.parse(source), indent=2)

                @staticmethod
                def dis(source: str) -> str:
                    """Disassemble a file."""
                    return str(dis.dis(source))

        class _(CliModule):
            @staticmethod
            def echo(*args: str) -> None:
                """Echo the given arguments."""
                print(args[0]) if len(args) == 1 else print(" ".join(args))

            @staticmethod
            def cat(path: str) -> None:
                """Print the contents of a file."""
                print(Path(path).read_text())

            @staticmethod
            def read(path: str) -> str:
                return Path(path).read_text()

            @staticmethod
            def sum(*args: str) -> float | int | None:
                """Sum the given arguments."""
                result = sum(map(float, args))
                if result:
                    if result.is_integer():
                        return int(result)
                    return result

            def exit(self) -> None:
                """Exit the program."""
                raise SystemExit


def main():
    app = AstExplorer()
    app.run()


if __name__ == "__main__":
    main()
