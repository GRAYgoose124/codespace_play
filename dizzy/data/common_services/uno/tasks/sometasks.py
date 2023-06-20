from dizzy import Task


class A(Task):
    description = "A task"

    @staticmethod
    def run(ctx):
        ctx["A"] = "A"
        return "A"


class B(Task):
    description = "B task"
    dependencies = ["A"]

    @staticmethod
    def run(ctx):
        ctx["B"] = f"{ctx['A']}B"
        return f"{ctx['A']}B"
