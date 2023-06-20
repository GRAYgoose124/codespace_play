from dizzy import Task


class A(Task):
    name = "A"
    description = "A task"

    @staticmethod
    def run(ctx):
        ctx["A"] = "A"
        return "A"


class B(Task):
    name = "B"
    description = "B task"
    dependencies = ["A"]

    @staticmethod
    def run(ctx):
        ctx["B"] = "B"
        return "B"
