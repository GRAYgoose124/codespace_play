#!/usr/bin/env python
from functools import wraps
import inspect
from itertools import chain
from traceback import print_exc
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

    @wraps(func)
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
    
    @validate
    def variadic_func[T](a: T, *args: T) -> T:
        return sum(*args) + a
    
    @validate
    def default_arg_func[T, U](a: T, b: U = 10) -> U:
        return b
    
    @validate
    def nested_generic_func[T, U](a: (T, U), b: [T]) -> dict:
        return {"first": a, "second": b}

    def test_validation(func, *args, **kwargs) -> bool:
        print(f"\nTesting {func.__name__} with {args=}, {kwargs=}...")
        try:
            func(*args, **kwargs)
            return True
        except ValidationError as e:
            pass
        except Exception as e:
            print_exc()
        return False
    
    def test_main():
        tests = [
            lambda: test_validation(mymod, 10, 3),
            lambda: test_validation(mymod, 10.0, 3.0),
            lambda: not test_validation(mymod, 10, 3.0),
            lambda: test_validation(mysum, 1, 2),
            lambda: not test_validation(mysum, 1, 2.0),
            lambda: not test_validation(badmysum, 1, 2),
            lambda: test_validation(variadic_func, 1, 2, 3, 4),
            lambda: test_validation(variadic_func, 1.0, 2.0, 3.0),
            lambda: test_validation(variadic_func, "a", "b", "c"),
            lambda: not test_validation(variadic_func, 1, 2.0),
            lambda: test_validation(default_arg_func, "Hello"),
            lambda: test_validation(default_arg_func, "Hello", 20),
            lambda: not test_validation(default_arg_func, "Hello", "World"),
            lambda: test_validation(nested_generic_func, (1, "a"), [1, 2, 3]),
            lambda: test_validation(nested_generic_func, ("a", 1.0), ["a", "b"]),
            lambda: not test_validation(nested_generic_func, (1, "a"), [1, "b"]),
        ]

        test_results = []
        for t in tests:
            test_results.append(t())
            if not test_results[-1]:
                print(f"Failed.")
            else:
                print(f"Passed.")

        all_failure_indices = [i for i, result in enumerate(test_results) if not result]
        all_failure_bodies = [inspect.getsource(tests[i]) for i in all_failure_indices]
        all_failures_list_str = "".join([f"  {i+1}: {body.strip()}\n" for i, body in zip(all_failure_indices, all_failure_bodies)])
        print(f"\n --- Test Results --- \n{all(test_results)=}\nFailures:\n{all_failures_list_str}({sum(test_results)}/{len(test_results)}) passed.")

    test_main()


if __name__ == '__main__':
    main()
