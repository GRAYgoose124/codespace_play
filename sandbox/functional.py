from functools import wraps


def take(it, n):
    """Take n elements from it."""
    if callable(it):
        it = it()

    for _ in range(n):
        yield next(it) 


class Partial:
    def __init__(self, f, *args, **kwargs):
        self.f, self.args, self.kwargs = f, args, kwargs
    
    def __call__(self, *args, **kwargs): 
        new_partial = Partial(self.f, *(*self.args, *args), **{**self.kwargs, **kwargs})

        try:
            return new_partial.f(*new_partial.args, **new_partial.kwargs)
        except TypeError:
            return new_partial

    def __repr__(self):
        return f'{self.f.__name__}({self.args}, {self.kwargs})'

    def __add__(self, other):
        if isinstance(other, Partial) and len(self.args):
            forward = self.args[-1]
            self.args = self.args[:-1]
            return self(other(forward))
        return self(other)

                    
            
            
def partial_map(f, it):
    for e in it:
        yield Partial(f, e)


def partial(*pargs, **pkwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return Partial(func, *(*pargs, *args), **{**pkwargs, **kwargs})
        return wrapper()
    return decorator

class Test:
    # TODO: unittest / assert
    @staticmethod
    def mysum(a, b, kw=None):
        return int.__add__(a, b)

    @partial(3)
    @staticmethod
    def psum(a, b, kw=None):
        return int.__add__(a, b)
    
    @staticmethod
    def partial_test():    
        a = Partial(Test.mysum)
        print('a', a)
        print('a()', a())
        print('a(2)', a(2))
        print('a(2)(2)', a(2)(2))
        print('a(2, 2)', a(2, 2))
        
        e = Test.psum
        print('e', e)
        print('e()', e())
        print('e(1)', e(1))

    @staticmethod
    def partial_map_test():
        a = partial_map(lambda x, y, z: x - y + z, range(10, 1, -1))
        print([pe(i)()(1) for i, pe in enumerate(a)])

    @staticmethod
    def partial_comp_test():
        # todo: fix + overloading such that partial doesn't interfere with result
        a = Partial(Test.mysum)
        b = Test.psum
        c = a + b
        d = a + b(1)
        e = a(1) + b(1)
        f = a(1) + b
        print(a, b, c(1, 2), d(1), e, f(1, 2, 3), sep='\n')

#Test.partial_test()
#Test.partial_map_test()
Test.partial_comp_test()
   