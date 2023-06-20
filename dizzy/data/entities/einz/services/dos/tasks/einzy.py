from dizzy import Task


class EinzyA(Task):
    """A task"""

    @staticmethod
    def run(ctx):
        ctx["EinzyA"] = "A"
        return "EinzyA"


class EinzyB(Task):
    """B task"""

    dependencies = ["EinzyA"]

    @staticmethod
    def run(ctx):
        ctx["B"] = f"{ctx['EinzyA']}B"
        return f"{ctx['EinzyA']}B"


class NotUsed(Task):
    """Ignored"""

    @staticmethod
    def run(ctx):
        return "Not used"
