from dataclasses import dataclass, field
from random import random


class Hero:
    def __init__(self):
        self.health = 100
        self.inventory = set()

    def hurt(self, amount):
        self.health -= amount

    def heal(self, amount):
        self.health += amount

    def has(self, item):
        return item in self.inventory

    def give(self, item):
        self.inventory.add(item)
        return True


hero = Hero()
Ally = object()


@dataclass
class Transition:
    pass_state: str
    condition: callable = None
    fail_state: str = "RETURN"


@dataclass
class Space:
    name: str
    transitions: list = field(default_factory=lambda: [Transition("RETURN")])
    on_enter: callable = None
    on_exit: callable = None


# RETURN is a special transition that can always be taken, it is based on a path stack
BEGIN = Space(
    "BEGIN",
    transitions=[
        Transition("TRIAL"),
        Transition("ALLY"),
    ],
)
TRIAL = Space("TRIAL", transitions=[Transition("CHALLENGE", lambda: hero.has(Ally))])
ALLY = Space("ALLY", on_enter=lambda: hero.give(Ally) and hero.heal(10))
CHALLENGE = Space(
    "CHALLENGE",
    transitions=[
        Transition("VICTORY", lambda: hero.has(Ally) and hero.health > 10, "DEFEAT")
    ],
)
VICTORY = Space("VICTORY", on_enter=lambda: print("YOU WON!"))  # implied RETURN
DEFEAT = Space(
    "DEFEAT",
    on_enter=lambda: hero.hurt(10) if random.random() < 0.5 else hero.hurt(20),
    transitions=[Transition("POST_DEFEAT", lambda: hero.health > 0, "END")],
)
POST_DEFEAT = Space("POST_DEFEAT")
END = Space("END", on_enter=lambda: print("GAME OVER"))


class GameEngine:
    def __init__(self, start_space):
        self.current_space = start_space
        self.path_stack = []

    def get_user_input(self):
        # Print options for the user to select
        print(
            f"\nYou are in the {self.current_space.name} space. What would you like to do?"
        )

        options = []
        for idx, transition in enumerate(self.current_space.transitions, 1):
            options.append(transition.pass_state)
            print(f"{idx}. Go to {transition.pass_state}")

        # Allow user to return if there's a previous state
        if self.path_stack:
            print(f"{len(options) + 1}. RETURN to previous state")
            options.append("RETURN")

        # Get user selection
        while True:
            choice = input("Choose an option: ")
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            print("Invalid choice. Please try again.")

    def enter_space(self):
        # Execute on_enter if available
        if self.current_space.on_enter:
            self.current_space.on_enter()

        while True:
            next_space_name = self.get_user_input()

            if next_space_name == "RETURN":
                self.current_space = self.path_stack.pop()
            else:
                transition = next(
                    filter(
                        lambda t: t.pass_state == next_space_name,
                        self.current_space.transitions,
                    )
                )
                if not transition.condition or transition.condition():
                    self.path_stack.append(self.current_space)
                    self.current_space = globals()[transition.pass_state]
                else:
                    print(f"Cannot move to {next_space_name}. Condition not met!")
                    continue

            break

    def play(self):
        while self.current_space.name != "END":
            self.enter_space()
        print("Thank you for playing!")


# Starting the game
game_engine = GameEngine(BEGIN)
game_engine.play()
