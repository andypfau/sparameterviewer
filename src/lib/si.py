from __future__ import annotations

import math
import locale
import re
import functools
import warnings
from dataclasses import dataclass



class SiFormat:


    PREFIXES = ((1e+18, 'E'), (1e+15, 'P'), (1e+12, 'T'), (1e+9, 'G'), (1e+6, 'M'), (1e+3, 'k'), (1.0, ''), (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p'), (1e-15, 'f'), (1e-18, 'a'))
    REX_FLOAT = r'[-+]?(?:\d+\.?|\.\d)\d*(?:[Ee][-+]?\d+)?'
    REX_SI_FLOAT = REX_FLOAT + r'\s*[fpnuµmkMGTE]?'
    

    def __init__(self, unit: str = '', *, digits: int = 3, prefixed: bool = True, remove_trailing_zeros: bool = True, signed: bool = False):
        self.unit, self.digits, self.prefixed, self.remove_trailing_zeros, self.signed = unit, digits, prefixed, remove_trailing_zeros, signed

    
    def __eq__(self, other) -> bool:
        if isinstance(other, SiFormat):
            return self.unit==other.unit and self.digits==other.digits and self.prefixed==other.prefixed and self.remove_trailing_zeros==other.remove_trailing_zeros and self.signed==other.signed
        return super().__eq__(other)


    @staticmethod
    def get_scale(value: float) -> "tuple[float,str]":
        
        if value==0:
            return 1.0, ''

        for f,p in SiFormat.PREFIXES:
            if abs(value)>=f:
                return f,p
        
        return SiFormat.PREFIXES[-1][0], SiFormat.PREFIXES[-1][1]
    

    @staticmethod
    def to_significant_digits(value: float, digits: int = 3) -> str:
        
        frac_digits = digits
        
        if value != 0:
            exp = int(math.floor(math.log10(abs(value))))
            frac_digits = max(0, digits-exp-1)
        
        return f'{value:.{frac_digits}f}'
    

    def format(self, value: float) -> str:
        if self.prefixed:
            factor,si_prefix = SiFormat.get_scale(value)
        else:
            factor,si_prefix = 1.0,''
        value_scaled = value / factor

        number = SiFormat.to_significant_digits(value_scaled, self.digits)
        if value > 0 and self.signed:
            number = '+' + number

        if self.remove_trailing_zeros:
            decimal_point = '.'  # f-strings always use a point
            while decimal_point in number and number.endswith('0'):
                number = number[:-1]
            if number.endswith(decimal_point):
                number = number[:-1]

        suffix = f'{si_prefix}{self.unit}'
        if len(suffix)>0:
            suffix = ' ' + suffix

        return number + suffix
    
    
    def parse(self, value: str) -> float:
        s = value.strip()
        if self.unit and len(s)>len(self.unit) and s.endswith(self.unit):
            s = s[:-len(self.unit)]
        
        factor = 1
        if len(s) > 1:
            for prefix_factor, prefix in SiFormat.PREFIXES:
                if s[-1] == prefix:
                    s = s[:-1]
                    factor = prefix_factor
                    break
        
        return float(s) * factor



@functools.total_ordering
class SiValue:

    def __init__(self, value: float|str, unit: str = '', *, spec: SiFormat = None):
        self._observers: list[callable[float,None]] = []

        if spec is not None:
            self.spec = spec
        else:
            self.spec = SiFormat(unit=unit)

        self._value: float

        if isinstance(value, complex):
            if value.imag != 0:
                warnings.warn(f'Constructing an Si from a complex number discards the imaginary part')
            self._value = value.real
        elif isinstance(value, str):
            self.parse(value)
        else:
            self._value = value

    
    def __eq__(self, other) -> bool:
        if isinstance(other, SiValue):
            return self._value==other._value and self.spec==other.spec
        return super().__eq__(other)

    
    def __ge__(self, other) -> bool:
        if isinstance(other, SiValue):
            return self._value>=other._value
        if isinstance(other, float) or isinstance(other, int):
            return self._value>=other
        return super().__ge__(other)
    

    def __repr__(self) -> str:
        return f'SiValue({self._value}{f",unit=\"{self.spec.unit}\"" if self.spec.unit else ""})'


    def __str__(self) -> str:
        return self.format()


    @property
    def value(self) -> float:
        return self._value
    @value.setter
    def value(self, value: float):
        self._value = value
        self._notify()


    def copy(self) -> SiValue:
        return SiValue(value=self._value, spec=self.spec)


    def reconstruct(self, value) -> SiValue:
        return SiValue(value=value, spec=self.spec)
    

    def format(self) -> str:
        return self.spec.format(self._value)
    

    def parse(self, value: str) -> SiValue:
        self._value = self.spec.parse(value)
        self._notify()
        return self


    def attach(self, callback: callable[float,None]):
        if callback in self._observers:
            return
        self._observers.append(callback)


    def _notify(self):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](self._value)
            except Exception as ex:
                del self._observers[i]



class SiRange:


    STR_WILDCARD = '*'
    STR_SEPARATOR = '…'


    def __init__(self, low: float = any, high: float = any, spec: SiFormat = SiFormat(), *, wildcard_value_low: any = any, wildcard_value_high: any = any, allow_both_wildcards: bool = True, allow_individual_wildcards: bool = True):
        self._observers: list[callable[tuple[float,float],None]] = []
        self._low, self._high, self.spec = low, high, spec
        self.wildcard_value_low, self.wildcard_value_high, self.allow_both_wildcards, self.allow_individual_wildcards = wildcard_value_low, wildcard_value_high, allow_both_wildcards, allow_individual_wildcards


    @property
    def low(self) -> float:
        return self._low
    @low.setter
    def low(self, value: float):
        self._low = value
        self._notify()


    @property
    def high(self) -> float:
        return self._high
    @high.setter
    def high(self, value: float):
        self._high = value
        self._notify()
    

    @property
    def low_is_wildcard(self) -> bool:
        return self._low == self.wildcard_value_low and (self.allow_both_wildcards or self.allow_individual_wildcards)
    @low_is_wildcard.setter
    def low_is_wildcard(self, value: bool):
        if value:
            if value == self.low_is_wildcard:
                return
            if not (self.allow_individual_wildcards or self.allow_both_wildcards):
                raise RuntimeError('Setting lower range value to wildcard is not allowed')
            self._low = self.wildcard_value_low
            self._notify()
        else:
            raise RuntimeError('Cannot un-set low wildcard directly; instead, set the low value to some numeric value')
    

    @property
    def high_is_wildcard(self) -> bool:
        return self._high == self.wildcard_value_high and (self.allow_both_wildcards or self.allow_individual_wildcards)
    @high_is_wildcard.setter
    def high_is_wildcard(self, value: bool):
        if value:
            if value == self.high_is_wildcard:
                return
            if not (self.allow_individual_wildcards or self.allow_both_wildcards):
                raise RuntimeError('Setting lower range value to wildcard is not allowed')
            self._high = self.wildcard_value_high
            self._notify()
        else:
            raise RuntimeError('Cannot un-set high wildcard directly; instead, set the high value to some numeric value')
    

    @property
    def both_are_wildcard(self) -> bool:
        return self._low==self.wildcard_value_low and self._high==self.wildcard_value_high and self.allow_both_wildcards
    @both_are_wildcard.setter
    def both_are_wildcard(self, value: bool):
        if value:
            if value == self.low_is_wildcard and self.high_is_wildcard:
                return
            if not self.allow_both_wildcards:
                raise RuntimeError('Setting both range values to wildcard is not allowed')
            self._low, self._high = self.wildcard_value_low, self.wildcard_value_high
            self._notify()
        else:
            raise RuntimeError('Cannot un-set wildcards directly; instead, set the low and high values to some numeric values')
    
    def __eq__(self, other) -> bool:
        if isinstance(other, SiRange):
            return self._low==other._low and self._high==other._high and self.spec==other.spec and self.wildcard_value_low==other.wildcard_value_low and self.wildcard_value_high==other.wildcard_value_high and self.allow_both_wildcards==other.allow_both_wildcards and self.allow_individual_wildcards==other.allow_individual_wildcards
        return super().__eq__(other)
    

    def __repr__(self) -> str:
        return f'SiRange({self._low},{self._high})'


    def __str__(self) -> str:
        return self.format()


    def copy(self) -> SiRange:
        return SiRange(low=self._low, high=self._high, spec=self.spec, wildcard_value_low=self.wildcard_value_low, wildcard_value_high=self.wildcard_value_high, allow_both_wildcards=self.allow_both_wildcards, allow_individual_wildcards=self.allow_individual_wildcards)
    

    def reconstruct(self, low, high) -> SiValue:
        return SiRange(low=low, high=high, spec=self.spec, wildcard_value_low=self.wildcard_value_low, wildcard_value_high=self.wildcard_value_high, allow_both_wildcards=self.allow_both_wildcards, allow_individual_wildcards=self.allow_individual_wildcards)


    def format(self) -> str:
        if self.low_is_wildcard and self.high_is_wildcard:
            if self.allow_both_wildcards:
                return SiRange.STR_WILDCARD
            if self.allow_individual_wildcards:
                return f'{SiRange.STR_WILDCARD} {SiRange.STR_SEPARATOR} {SiRange.STR_WILDCARD}'
        
        low_str  = SiRange.STR_WILDCARD if self.low_is_wildcard  else str(SiValue(self._low,  spec=self.spec))
        high_str = SiRange.STR_WILDCARD if self.high_is_wildcard else str(SiValue(self._high, spec=self.spec))
        return f'{low_str} {SiRange.STR_SEPARATOR} {high_str}'
    

    def parse(self, value: str) -> SiRange:
        s = value.strip()

        if self.allow_both_wildcards:
            if s == SiRange.STR_WILDCARD:
                self._low, self._high = self.wildcard_value_low, self.wildcard_value_high
                return self
        
        if self.allow_individual_wildcards:
            if re.match(r'\*(\s+|\s*(;|,|…|\.\.|\.\.\.)\s*)\*', s):
                self._low, self._high = self.wildcard_value_low, self.wildcard_value_high
                return self
        
        def set_low_high(part_a: str, part_b: str):
            
            part_a, part_b = part_a.strip(), part_b.strip()
            
            if part_a == SiRange.STR_WILDCARD:
                a = self.wildcard_value_low
            else:
                a = self.spec.parse(part_a)
            
            if part_b == SiRange.STR_WILDCARD:
                b = self.wildcard_value_high
            else:
                b = self.spec.parse(part_b)
            
            if a != self.wildcard_value_low and b != self.wildcard_value_high and a > b:
                self._low, self._high = b, a
            else:
                self._low, self._high = a, b

        # separated by whitespace?
        parts = re.split(r'\s+', s)
        if len(parts) == 2:
            set_low_high(parts[0], parts[1])
            return self

        # separated by any separator other than "-"?
        parts = re.split(r'\s*(?:;|,|…|\.\.\.|\.\.)\s*', s)
        if len(parts) == 2:
            set_low_high(parts[0], parts[1])
            return self

        # separated by "-"? Be careful not to mis-interpret it as a minus-sign!
        parts = [part for part in re.split(r'(-)', s) if part.strip()!='']
        if len(parts)==3 and parts[1]=='-':
            # e.g. "1 - 2"
            set_low_high(parts[0], parts[2])
            return self
        if len(parts)==4 and parts[0]=='-' and parts[2]=='-':
            # e.g. "-1 - 2"
            set_low_high(parts[0]+parts[1], parts[3])
            return self
        if len(parts)==4 and parts[1]=='-' and parts[2]=='-':
            # e.g. "1 - -2"
            set_low_high(parts[0], parts[2]+parts[3])
            return self
        if len(parts)==5 and parts[0]=='-' and parts[2]=='-' and parts[3]=='-':
            # e.g. "-1 - -2"
            set_low_high(parts[0]+parts[1], parts[3]+parts[4])
            return self

        raise ValueError(f'Cannot parse range "{s}"; parts are {parts}')


    def attach(self, callback: callable[tuple[float,float],None]):
        if callback in self._observers:
            return
        self._observers.append(callback)


    def _notify(self):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](self._low, self._high)
            except Exception as ex:
                del self._observers[i]
