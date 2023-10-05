import functools as ft
import itertools as it


def I(x):
    return x


def K(x):
    return lambda y: x


def S(x):
    return lambda y: lambda z: x(z)(y(z))


def _I(x):
    return S(K)(K)(x)


assert I(1) == _I(1)
