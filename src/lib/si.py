import math, cmath, locale
from dataclasses import dataclass
from os import stat
from unicodedata import decimal
import numpy as np
import re


@dataclass
class SiFmt:
    unit: str = ''
    significant_digits: int = 3
    use_si_prefix: bool = True
    remove_trailing_zeros: bool = True
    force_sign: bool = False


class Si:

    @staticmethod
    def get_scale(value: float) -> "tuple[float,str]":
        
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
        if isinstance(value, complex):
            if value.imag == 0:
                value = value.real
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


def parse_si_range(s: str, *, wildcard_low=-1e99, wildcard_high=+1e99, allow_both_wildcards=True, allow_individual_wildcards=True) -> tuple[any,any]:
    """
    Parse a numeric range, given as float or SI-prefixed numbers.
    Returns the range `(a,b)` if successful, or raises ValueError on invalid input.
    Suported formats include e.g.:
    - "1m-1G": ragne from 1e-3 to 1e9
    - "*-1G": range from `wildcard_low` to 1e9
    - "1m-*": range from 1e-3 to `wildcard_high`
    - "", "*": any range
    `wildcard_low` and `wildcard_high` can be disabled by setting them to None.
    """
    
    REX_FLOAT = r'[-+]?(?:\d+\.?|\.\d)\d*(?:[Ee][-+]?\d+)?'
    REX_SI_FLOAT = REX_FLOAT + r'\s*[fpnuµmkMGTE]?'
    REX_SEPARATOR = r'(?:-|;|,|\.\.|\.\.\.)'

    s = s.strip()
    if allow_both_wildcards:
        if(s=='*') or re.match(r'\*\s*'+REX_SEPARATOR+r'\s*\*', s):
            return wildcard_low, wildcard_high

    def parse_si_float(s):
        PREFIXES = {'f':1e-15, 'p':1e-12, 'n':1e-9, 'u': 1e-6, 'µ': 1e-6, 'm':1e-3, 'k':1e3, 'M':1e6, 'G':1e9, 'T':1e12, 'E':1e15}
        factor = 1
        if len(s) >= 2:
            if s[-1] in PREFIXES.keys():
                factor = PREFIXES[s[-1]]
                s = s[:-1]
        return factor * float(s)

    if allow_individual_wildcards and (m := re.match(r'\*\s*'+REX_SEPARATOR+r'\s*('+REX_SI_FLOAT+r')\s*$', s)):
        b = parse_si_float(m.group(1))
        return wildcard_low, b
    
    if allow_individual_wildcards and (m := re.match(r'^\s*('+REX_SI_FLOAT+r')\s*'+REX_SEPARATOR+r'\s*\*\s*$', s)):
        a = parse_si_float(m.group(1))
        return a, wildcard_high
    
    if (m := re.match(r'^\s*('+REX_SI_FLOAT+r')\s*'+REX_SEPARATOR+r'\s*('+REX_SI_FLOAT+r')\s*$', s)):
        a, b = parse_si_float(m.group(1)), parse_si_float(m.group(2))
        if a <= b:
            return a, b

    raise ValueError(f'Cannot parse range "{s}')


def format_si_range(a, b, allow_total_wildcard=False) -> str:
    if allow_total_wildcard and a is any and b is any:
        return '*'
    result = ''
    if a is any:
        result += '*'
    else:
        result += str(Si(a))
    result += ' .. '
    if b is any:
        result += '*'
    else:
        result += str(Si(b))
    return result
