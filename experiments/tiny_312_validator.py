#!/usr/bin/env python
import inspect


class ValidationError(TypeError):
    pass


def check_binding(name, arg, context):
    Gbinds, Gbins, Gs, argspec = context
    if name in argspec.annotations:
        for G in Gs:
            if G == argspec.annotations[name]: # is?
                if Gbinds[G] is None:
                    Gbinds[G] = type(arg)
                elif Gbinds[G] != type(arg):
                    raise ValidationError(f"Generic {G} bound to different types: {Gbinds[G]}, but arg is {type(arg)}")
                Gbins[G].append(arg)


def validate(func):
    """Validate the arguments of a function."""
    argspec = inspect.getfullargspec(func)

    Gs = func.__type_params__

    def wrapper(*args, **kwargs):
        Gbinds = {G: None for G in Gs}
        Gbins = {G: [] for G in Gs}

        context = (Gbinds, Gbins, Gs, argspec)
        for name, arg in zip(argspec.args, args):
            check_binding(name, arg, context)
            
        for name, arg in kwargs.items():
            check_binding(name, arg, context)

        generics_are_bound = all(val is not None or len(bound)==0 for val, bound in zip(Gbinds.values(), Gbins.values()))
        if generics_are_bound:
            result = func(*args, **kwargs)
            # validate result against return type
            if argspec.annotations.get("return"):
                if type(result) not in argspec.annotations["return"].__constraints__:
                    raise ValidationError(f"Return type {argspec.annotations['return']} does not match {type(result)}")
            return result
        else:
            raise ValidationError(f"{Gbinds=} {Gbins=}")

    return wrapper


def main():
    @validate
    def mymod[T](a: T, b: T):
        return a % b

    @validate
    def mysum[T, W: (int, float)](a: T, b: T) -> W:
        return (a + b)

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
