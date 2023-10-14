from collections.abc import Iterable
from typing import Generic, TypeVar, List, Type, Dict, Callable

T = TypeVar("T")


class TypeRegistry:
    conversions = {}
    mixin_registry = {}

    @classmethod
    def register(
        cls,
        source: Type,
        target: Type,
        _to: Callable,
        _from: Callable | None = None,
    ):
        cls.conversions.setdefault(source, {})[target] = _to
        if target not in cls.conversions and _from:
            cls.conversions.setdefault(target, {})[source] = _from

    @classmethod
    def convert_item(cls, source_item, target_type):
        source_type = type(source_item)
        if (
            source_type in cls.conversions
            and target_type in cls.conversions[source_type]
        ):
            return cls.conversions[source_type][target_type](source_item)
        return source_item

    @classmethod
    def get_mixin_for_type(cls, type_: Type) -> Type:
        return cls.mixin_registry.get(type_)


class AutoContainer(Generic[T], Iterable):
    def __init__(self, items: List[T]) -> None:
        self.items = items

    def __iter__(self):
        return iter(self.items)

    def __getattr__(self, name):
        for item_type, mixin in TypeRegistry.mixin_registry.items():
            if hasattr(mixin, name):
                method = getattr(mixin, name)
                return lambda: method(self)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )


class MixinMeta(type):
    def __new__(cls, name, bases, attrs):
        mixin = super().__new__(cls, name, bases, attrs)

        if mixin.__base__ not in TypeRegistry.mixin_registry:
            TypeRegistry.mixin_registry[mixin.__base__] = mixin

        for key, value in attrs.items():
            if callable(value):
                setattr(mixin, key, cls.wrap_method(value))

        return mixin

    @staticmethod
    def wrap_method(method):
        def wrapper(container):
            target_type = TypeRegistry.get_mixin_for_type(type(container))

            converted_items = [
                TypeRegistry.convert_item(item, target_type) for item in container.items
            ]

            result = method(converted_items)

            container.items = [
                TypeRegistry.convert_item(item, type(container.items[i]))
                for i, item in enumerate(converted_items)
            ]

            return result

        return wrapper


class IntMixin(int, metaclass=MixinMeta):
    @staticmethod
    def double(items):
        for i, item in enumerate(items):
            if isinstance(item, int):
                items[i] = item * 2


class StrMixin(str, metaclass=MixinMeta):
    @staticmethod
    def capitalize(items):
        for i, item in enumerate(items):
            if isinstance(item, str):
                items[i] = item.capitalize()


if __name__ == "__main__":
    TypeRegistry.register(str, int, _to=lambda s: int(s), _from=lambda i: str(i))

    int_container = AutoContainer([1, 2, 3])
    int_container.double()
    print(list(int_container))  # [2, 4, 6]

    str_container = AutoContainer(["a", "b", "c"])
    str_container.capitalize()
    print(list(str_container))  # ['A', 'B', 'C']

    str_container_with_numbers = AutoContainer(["1", "2", 3])
    str_container_with_numbers.double()
    print(list(str_container_with_numbers))  # ['2', '4', '6']
