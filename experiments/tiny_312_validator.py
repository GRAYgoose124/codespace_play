#!/usr/bin/env python
import inspect
import logging
from functools import wraps
from itertools import chain
from typing import TypeVar


log = logging.getLogger(__name__)


class ValidationError(TypeError):
    pass


def check_binding(annotation, arg, Gbinds):
    if isinstance(annotation, tuple):
        if isinstance(arg, tuple) and len(annotation) == len(arg):
            for a, b in zip(annotation, arg):
                check_binding(a, b, Gbinds)
        else:
            log.debug(type(annotation), type(arg))
            raise ValidationError(f"{arg=} is not valid for {annotation=}")
    elif isinstance(annotation, TypeVar):
        if Gbinds[annotation][0] is None:
            Gbinds[annotation][0] = type(arg)
        elif Gbinds[annotation][0] != type(arg):
            raise ValidationError(f"Generic {annotation} bound to different types: {Gbinds[annotation][0]}, but arg is {type(arg)}")
        Gbinds[annotation][1].append(arg)
    elif isinstance(annotation, list):
        if isinstance(arg, list):
            for a in arg:
                check_binding(annotation[0], a, Gbinds)
        else:
            raise ValidationError(f"{arg=} is not valid for {annotation=}")


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

            if "return" in argspec.annotations:
                return_spec = argspec.annotations["return"]
                log.debug("%s %s %s", argspec.annotations, type(result), return_spec)

                return_doesnt_equal_result = return_spec != type(result)
                return_isnt_in_constraints = hasattr(return_spec, '__constraints__') and type(result) not in return_spec.__constraints__
                if return_doesnt_equal_result and return_isnt_in_constraints:
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
    def variadic_func[T](a: T, *args: list[T]) -> T:
        if isinstance(a, str):
            return f"{a}".join(args)
        return sum(args, a)
    
    @validate
    def default_arg_func[T, U: (int, float)](a: T, b: U = 10) -> U:
        return b
    
    @validate
    def nested_generic_func[T, U](a: (T, U), b: list[T]) -> dict:
        return {"first": a, "second": b}

    def test_validation(func, *args, **kwargs) -> bool:
        log.info(f"Testing {func.__name__} with {args=}, {kwargs=}...")
        try:
            func(*args, **kwargs)
            return True
        except ValidationError as e:
            pass
        except Exception as e:
            log.exception(e)
        return False

    def test_runner(tests, level=logging.INFO):
        logging.basicConfig(level=level, format="%(levelname).4s | %(message)s")

        test_results = []
        for t in tests:
            test_results.append(t())
            if not test_results[-1]:
                log.warning(f"Failed.")
            else:
                log.info(f"Passed.")

        failed_test_idxs = [i for i, result in enumerate(test_results) if not result]
        fail_out = "".join([f"  {i+1}: {body.strip()}\n" for i, body in zip(failed_test_idxs, [inspect.getsource(tests[i]) for i in failed_test_idxs])])
        print(f"\n --- Test Results --- \n{all(test_results)=}\nFailures:\n{fail_out}({sum(test_results)}/{len(test_results)}) passed.")

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

        test_runner(tests)

    test_main()


if __name__ == '__main__':
    main()
