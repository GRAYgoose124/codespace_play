from dizzy import Task


class C(Task):
    name = "C"
    description = "C task"

    @staticmethod
    def run():
        return "C"


class D(Task):
    name = "D"
    description = "D task"

    @staticmethod
    def run():
        return "D"
