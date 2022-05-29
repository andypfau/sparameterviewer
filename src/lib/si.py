import math, cmath, locale
from dataclasses import dataclass
from os import stat
from unicodedata import decimal
import numpy as np


@dataclass
class SiFmt:
    unit: str = ''
    significant_digits: int = 3
    use_si_prefix: bool = True
    remove_trailing_zeros: bool = True
    force_sign: bool = False


class Si:

    @staticmethod
    def get_scale(value: float) -> "tuple(float,str)":
        
        if value==0:
            return 1.0, ''

        PREFIXES = (
            (1e+18, 'E'),
            (1e+15, 'P'),
            (1e+12, 'T'),
            (1e+9, 'G'),
            (1e+6, 'M'),
            (1e+3, 'k'),
            (1.0, ''),
            (1e-3, 'm'),
            (1e-6, 'µ'),
            (1e-9, 'n'),
            (1e-12, 'p'),
            (1e-15, 'f'),
            (1e-18, 'a'),
        )

        for f,p in PREFIXES:
            if abs(value)>=f:
                return f,p
        
        return PREFIXES[-1][0], PREFIXES[-1][1]
    

    @staticmethod
    def to_significant_digits(value: float, significant_digits: int = 3) -> str:
        frac_digits = significant_digits
        if value != 0:
            exp = int(math.floor(math.log10(abs(value))))
            frac_digits = max(0, significant_digits-exp-1)
        return f'{value:.{frac_digits}f}'


    def __init__(self, value: float, unit: str = '', significant_digits: int = 3, use_si_prefix: bool = True, remove_trailing_zeros: bool = True, force_sign: bool = False, si_fmt: SiFmt = None):
        self.value = value
        if si_fmt is not None:
            self.format = si_fmt
        else:
            self.format = SiFmt(unit, significant_digits, use_si_prefix, remove_trailing_zeros, force_sign)


    def __str__(self):
        if self.format.use_si_prefix:
            factor,si_prefix = Si.get_scale(self.value)
        else:
            factor,si_prefix = 1.0,''
        value_scaled = self.value / factor

        number = Si.to_significant_digits(value_scaled, self.format.significant_digits)
        if self.value > 0 and self.format.force_sign:
            number = '+' + number

        if self.format.remove_trailing_zeros:
            decimal_point = locale.localeconv()['decimal_point']
            while decimal_point in number and number.endswith('0'):
                number = number[:-1]
            if number.endswith(decimal_point):
                number = number[:-1]

        suffix = f'{si_prefix}{self.format.unit}'
        if len(suffix)>0:
            suffix = ' ' + suffix

        return number + suffix
    

    def __repr__(self):
        return self.__str__()
