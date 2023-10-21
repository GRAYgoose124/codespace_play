#!/usr/bin/env python
import inspect
from itertools import chain
from typing import TypeVar


class ValidationError(TypeError):
    pass


def check_binding(annotation, arg, Gbinds):
    if isinstance(annotation, tuple):
        if type(arg) not in annotation:
            raise ValidationError(f"{arg} is not valid for {annotation}")
    elif isinstance(annotation, TypeVar):
        if Gbinds[annotation][0] is None:
            Gbinds[annotation][0] = type(arg)
        elif Gbinds[annotation][0] != type(arg):
            raise ValidationError(f"Generic {annotation} bound to different types: {Gbinds[annotation][0]}, but arg is {type(arg)}")
        Gbinds[annotation][1].append(arg)
    else:
        if type(arg) != annotation:
            raise ValidationError(f"{arg} is not valid for {annotation}")


def validate(func):
    """Validate the arguments of a function."""
    argspec, generics = inspect.getfullargspec(func), func.__type_params__

    def wrapper(*args, **kwargs):
        Gbinds = {G: [None, []] for G in generics}

        for name, arg in chain(zip(argspec.args, args), kwargs.items()):
            annotation = argspec.annotations.get(name)
            if annotation is not None:
                check_binding(annotation, arg, Gbinds)

        if all(val is not None or len(bound)==0 for val, bound in Gbinds.values()):
            result = func(*args, **kwargs)
            if "return" in argspec.annotations and type(result) not in argspec.annotations["return"].__constraints__:
                raise ValidationError(f"Return type {argspec.annotations['return']} does not match {type(result)}")
            return result
        else:
            raise ValidationError(f"{Gbinds=}")

    return wrapper


def main():
    @validate
    def mymod[T](a: T, b: T):
        return a % b

    @validate
    def mysum[T, W: (int, float)](a: T, b: T) -> W:
        return float(a + b)

    @validate
    def badmysum[T, W: (int, float)](a: T, b: T) -> W:
        return str(a + b)

    def test_validation(func, *args, should_fail=False, **kwargs) -> bool:
        try:
            func(*args, **kwargs)
            if should_fail:
                return False
            else:
                return True
        except ValidationError as e:
            if should_fail:
                return True
            else:
                return False

    tests = [
        test_validation(mymod, 10, 3),
        test_validation(mymod, 10.0, 3.0),
        test_validation(mymod, 10, 3.0, should_fail=True),
        test_validation(mysum, 1, 2),
        test_validation(mysum, 1, 2.0, should_fail=True),
        test_validation(badmysum, 1, 2, should_fail=True)
    ]

    print(f"{all(tests)=}")


if __name__ == '__main__':
    main()
