from dizzy import Task


class C(Task):
    name = "C"
    description = "C task"
    dependencies = ["B"]

    @staticmethod
    def run(ctx):
        ctx["C"] = "C"
        return f"{ctx['B']}C"


class D(Task):
    name = "D"
    description = "D task"

    @staticmethod
    def run(ctx):
        ctx["D"] = "D"
        return "D"
