from dizzy import Task


class A(Task):
    description = "A task"

    @staticmethod
    def run():
        return "A"


class B(Task):
    name = "B"
    description = "B task"
    depends_on = ["A"]

    @staticmethod
    def run():
        return "B"
