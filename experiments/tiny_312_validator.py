#!/usr/bin/env python
import inspect
import logging
from functools import wraps
from itertools import chain
from typing import Sequence, TypeVar


log = logging.getLogger(__name__)


class ValidationError(TypeError):
    pass


def check_binding(ann, arg, Gbinds):
    log.debug(f"{ann=}:{type(ann)} {arg=} {Gbinds=}")

    if hasattr(ann, "__constraints__") and len(ann.__constraints__):
        log.debug(f"{ann} {ann.__constraints__}")
        if type(arg) not in ann.__constraints__:
            raise ValidationError(f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}")

    def handle_typevar():
        if Gbinds[ann][0] is None:
            Gbinds[ann][0] = type(arg)
        elif Gbinds[ann][0] != type(arg):
            raise ValidationError(f"Generic {ann} bound to different types: {Gbinds[ann][0]}, but arg is {type(arg)}")
        Gbinds[ann][1].append(arg)

    def handle_sequence():
        if isinstance(arg, tuple) and len(ann) == len(arg):
            for a, b in zip(ann, arg):
                check_binding(a, b, Gbinds)
        elif isinstance(arg, list):
            for a in arg:
                check_binding(ann[0], a, Gbinds)
        else:
            raise ValidationError(f"{arg=} is not valid for {ann=}")

    def handle_callable():
        if not ann(arg):
            raise ValidationError(f"{arg=} is not valid for {ann.__name__}")

    type_handlers = {
        TypeVar: handle_typevar,
        (list, tuple): handle_sequence,
        callable: handle_callable,
    }

    for type_check, handler in type_handlers.items():
        if isinstance(type_check, Sequence):
            if any(isinstance(ann, t) for t in type_check):
                handler()
                return
        if isinstance(ann, type_check):
            handler()
            return

    raise ValidationError(f"Type {type(ann)} is not handled.")


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
                ret_ann = argspec.annotations["return"]
                log.debug("annotations=%s result_type=%s return_spec=%s", argspec.annotations, type(result), ret_ann)


                if ret_ann != type(result):
                    check_binding(ret_ann, result, Gbinds)
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
    def variadic_func[T, *Ts](a: T, *args: [T]) -> T:
        if isinstance(a, str):
            return f"{a}".join(args)
        return sum(args + (a,),)
    
    @validate
    def default_arg_func[T, U: (int, float)](a: T, b: U = 10) -> U:
        return b
    
    @validate
    def nested_generic_func[T, U](a: (T, U), b: [T]) -> dict:
        return {"first": a, "second": b}

    def test_validation(func, *args, **kwargs) -> bool:
        global i
        log.info(f"{i}. Testing {func.__name__} with {args=}, {kwargs=}...")
        i += 1
        try:
            func(*args, **kwargs)
            return True
        except ValidationError as e:
            log.error(e.with_traceback(None))
        except Exception as e:
            log.exception(e)
        return False

    def test_runner(tests, level=logging.DEBUG):
        logging.basicConfig(level=level, format="%(levelname).4s | %(message)s")

        test_results = []
        for t in tests:
            test_results.append(t())
            if not test_results[-1]:
                log.warning(f"Failed.\n")
            else:
                log.info(f"Passed.\n")

        failed_test_idxs = [i for i, result in enumerate(test_results) if not result]
        fail_out = "".join([f"  {i}: {body.strip()}\n" for i, body in zip(failed_test_idxs, [inspect.getsource(tests[i]) for i in failed_test_idxs])])
        print(f"\n --- Test Results --- \n{all(test_results)=}\nFailures:\n{fail_out}({sum(test_results)}/{len(test_results)}) passed.")

    def test_main():
        global i
        i = 0
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
