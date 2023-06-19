# class Typist(type):
#     """ Metaclass for classes that have a __hardtype__ attribute."""

#         def __new__(cls, name, bases, attrs):
#             attrs["__hardtype__"] = name
#             return super().__new__(cls, name, bases, attrs)


import ast
import inspect
import textwrap


# class ASTDebug(type):
#     """Dropin metaclass to debug the AST of a class.

#     when you print out the class, it will print out the AST of the __init__ method.

#     """

#     @staticmethod
#     def debug_wrapper(name, func):
#         def wrapper(*args, **kwargs):
#             print(f"Calling {name} with {args=}, {kwargs=}")
#             return func(*args, **kwargs)

#         return wrapper

#     def __new__(cls, name, bases, attrs):
#         for name, attr in attrs.items():
#             if inspect.isfunction(attr):
#                 print(name, ast.dump(ast.parse(inspect.getsource(attr))))
#                 attrs[name] = ASTDebug.debug_wrapper(name, attr)

#         return super().__new__(cls, name, bases, attrs)


class DebugMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs = DebugMeta._add_debugging(attrs)

        attrs["debug_ast"] = lambda self: DebugMeta._ast_str(self.__class__)
        if "__str__" not in attrs:
            attrs["__str__"] = lambda self: DebugMeta._ast_str(
                self.__class__, show_ast=False
            )
        else:
            attrs[
                "__str__"
            ] = (
                lambda self: f"DebugOut: {attrs['debug_ast']()}\n Original: {attrs['__str__']()}"
            )

        return super().__new__(cls, name, bases, attrs)

    @staticmethod
    def _ast_str(cls, show_ast=True):
        source_code = inspect.getsource(cls)
        tree = ast.parse(source_code)

        # Print the class name
        s = f"Class: {cls.__name__}\n"

        # Print the AST of each method
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_ast = ast.dump(node, indent=2, include_attributes=False)
                pfx = "\t\t"

                s += f"\tMethod: {node.name}\n"

                if show_ast:
                    s += f"{textwrap.indent(method_ast, prefix=pfx)}\n"

        return s

    @staticmethod
    def _add_debugging(attrs):
        for attr_name, attr_value in attrs.items():
            if callable(attr_value):
                attrs[attr_name] = DebugMeta._debug_wrapper(attr_value)

        return attrs

    @staticmethod
    def _debug_wrapper(method):
        def wrapped(*args, **kwargs):
            print(f"| Calling: {method.__name__} with {args=}, {kwargs=}")
            results = method(*args, **kwargs)
            print(f"| {method.__name__} returned {results}")
            return results

        return wrapped


class Demo(metaclass=DebugMeta):
    def __init__(self, name: str):
        self.name = name

    @staticmethod
    def deco(func):
        def wrapper(*args, **kwargs):
            print("Decorator called")
            return func(*args, **kwargs)

        return wrapper

    def some_method(self):
        """This is a docstring."""
        pass

    @deco
    def some_other_method(self):
        pass


if __name__ == "__main__":
    print(Demo("test"))
