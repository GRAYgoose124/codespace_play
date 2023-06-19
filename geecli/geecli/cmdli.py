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
    def __init__(self):
        import readline

        self._commands = {}
        self._command = None

        self._unknown_handler = None

        self.add_command("help", self.help)
        self.add_command("exit", lambda: True)

    def run(self, command) -> bool:
        if command.startswith("/"):
            command = command[1:]
            if command in self._commands:
                try:
                    self._commands[command]()
                except CMDException as e:
                    print(f"CMD Error: {e}")
                except Exception as e:
                    print(f"Python Error: {e}")
                except KeyboardInterrupt:
                    print("KeyboardInterrupt")
                    raise CMDExit
            else:
                self.run_unk_handler(command)
        else:
            self.run_not_slash(command)

    def loop(self):
        try:
            while True:
                command = input("> ")
                self.run(command)
        except StopIteration:
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
