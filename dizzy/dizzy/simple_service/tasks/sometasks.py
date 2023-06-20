from dizzy import Task


class A(Task):
    name = "A"
    description = "A task"

    @staticmethod
    def run():
        return "A"


class B(Task):
    name = "B"
    description = "B task"

    @staticmethod
    def run():
        return "B"
