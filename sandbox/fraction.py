from math import pi


class Fraction:
    def __init__(self, int, fract):
        self.int = int
        self.fract = fract
        
    def as_dec(self):
        return self.int / self.fract
        
    def __str__(self):
        return f'{self.int}/{self.fract}'

    def __eq__(self, other):
        True if self.int == other.int and self.fract == other.fract else False
        
    def __lt__(self, other):
        True if self.int < other.int and self.fract < other.fract else False

    def __gt__(self, other):
        True if self.int > other.int and self.fract > other.fract else False
    
    @staticmethod
    def to_frac(dec, precision=100, bounds=((0, 1), (1, 1))):
        left, right = (Fraction(*bounds[0]), Fraction(*bounds[1]))
        current = None
        for i in range(precision):
            current = Fraction(left.int + right.int , left.fract + right.fract)
            cdec = current.as_dec()

            if dec == cdec:
                return current
            elif dec <= cdec:
                right = current
            elif dec > cdec:
                left = current

        return current

 
if __name__ == '__main__':
    print(f'0.33... ~= {Fraction.to_frac(0.333)}')
    print(f'{pi} ~= {Fraction.to_frac(pi, bounds=((0, 1), (4, 1)))}')
    print(f'0.25 ~= {Fraction.to_frac(.25)}')