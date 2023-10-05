import sympy as sp

magic = 0x5F3759DF

# check magic=2n+1
assert magic % 2 == 1
# check magic=2^n + 1
assert sp.isprime(magic - 1)
