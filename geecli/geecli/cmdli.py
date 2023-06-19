import sys


class CMDException(Exception):
    pass


class CMDExit(StopIteration):
    pass


def demo_cmd(a, b):
    """This is a demo command"""
    print(f"demo_cmd: {a}, {b}")


def demo_cmd2(a, b):
    """This is a demo command 2"""
    print(f"demo_cmd2: {a}, {b}")


class CLI:
    def __init__(self, command_char="/", prompt_str="> "):
        if "readline" not in sys.modules:
            import readline

        self.command_char = command_char
        self.prompt_str = prompt_str

        self._commands = {}
        self._command = None

        self._unknown_handler = None
        self._not_slash_handler = None

        self.add_command("help", self.help)
        self.register_commands()

        self.__post_init__()

    def __post_init__(self):
        pass

    @staticmethod
    def command(func):
        """decorator for marking method as a command"""
        func.is_command = True
        return func

    @staticmethod
    def not_slash(func):
        """decorator for marking method as the not_slash_handler"""
        func.is_not_slash = True
        return func

    @staticmethod
    def unknown(func):
        """decorator for marking method as the unknown_handler"""
        func.is_unknown = True
        return func

    def register_commands(self):
        for name in dir(self):
            func = getattr(self, name)
            if callable(func):
                if hasattr(func, "is_command") and func.is_command:
                    self.add_command(name, func)
                if hasattr(func, "is_not_slash") and func.is_not_slash:
                    self.set_not_slash_handler(func)
                if hasattr(func, "is_unknown") and func.is_unknown:
                    self.set_unknown_handler(func)

    def run(self, command) -> bool:
        if self.command_char is None or command.startswith(self.command_char):
            if self.command_char is not None:
                command = command[1:]

            if command in self._commands:
                try:
                    self._commands[command]()
                except CMDException as e:
                    print(f"CMD Error: {e}")
                except CMDExit:
                    raise CMDExit
                except KeyboardInterrupt:
                    print("KeyboardInterrupt")
                    raise CMDExit
                except Exception as e:
                    print(f"Python Error: {e}")
            else:
                self.run_unk_handler(command)
        else:
            self.run_not_slash(command)

    def loop(self):
        try:
            while True:
                command = input(self.prompt_str)
                self.run(command)
        except CMDExit:
            pass

    def run_not_slash(self, command):
        if self._not_slash_handler is not None:
            self._not_slash_handler(command)
        else:
            pass

    def run_unk_handler(self, command):
        if self._unknown_handler is not None:
            self._unknown_handler(command)
        else:
            print(f"Unknown command: {command}")

    def set_not_slash_handler(self, func):
        self._not_slash_handler = func

    def set_unknown_handler(self, func):
        self._unknown_handler = func

    def add_command(self, name, func):
        self._commands[name] = func

    def add_commands(self, commands: dict):
        self._commands.update(commands)

    def help(self):
        """Print help for all commands"""
        print("Available commands:")
        for name, func in self._commands.items():
            print(f"{name}: {func.__doc__}")


def main():
    cli = CLI()
    cli.add_command("demo", demo_cmd)
    cli.add_command("demo2", demo_cmd2)
    cli.loop()
