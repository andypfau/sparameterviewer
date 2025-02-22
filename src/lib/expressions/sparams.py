from ..structs import SParamFile
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..utils import sanitize_filename
from ..citi import CitiWriter

import skrf, math, os
import numpy as np
import fnmatch
import logging
import scipy.signal
import os
import re



class SParam:


    plot_fn: "callable[[np.ndarray,np.ndarray,complex,str,str], None]"


    def __init__(self, name: str, f: np.ndarray, s: np.ndarray, z0: float):
        self.name, self.f, self.s, self.z0 = name, f, s, z0
    

    @staticmethod
    def _adapt_f(a: "SParam", b: "SParam") -> "tuple(skrf.Network)":
        if len(a.f)==len(b.f):
            if all(af==bf for af,bf in zip(a.f, b.f)):
                return a,b
        f_min = max(min(a.f), min(b.f))
        f_max = min(max(a.f), max(b.f))
        f_new = np.array([f for f in a.f if f_min<=f<=f_max])
        freq_new = skrf.Frequency.from_f(f_new, unit='Hz')
        a_nw = skrf.Network(f=a.f, s=a.s, f_unit='Hz').interpolate(freq_new)
        b_nw = skrf.Network(f=b.f, s=b.s, f_unit='Hz').interpolate(freq_new)
        return a_nw,b_nw
    

    @staticmethod
    def _op(a: "SParam", b: "SParam", op: "callable") -> "SParam":
        if isinstance(a, (int,float,complex,np.ndarray)):
            return SParam(b.name, b.f, op(a,np.array(np.ndarray.flatten(b.s))), z0=b.z0)
        if isinstance(b, (int,float,complex,np.ndarray)):
            return SParam(a.name, a.f, op(np.array(np.ndarray.flatten(a.s)),b), z0=a.z0)
        a_nw, b_nw = SParam._adapt_f(a, b)
        a_s = np.array(np.ndarray.flatten(a_nw.s))
        b_s = np.array(np.ndarray.flatten(b_nw.s))
        c_s = op(a_s, b_s)
        return SParam(a.name, a_nw.f, c_s, a_nw.z0)

        
    def __truediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a/b)


    def __rtruediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a/b)

        
    def __mul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a*b)


    def __rmul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a*b)

        
    def __pow__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a**b)


    def __rpow__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a**b)

        
    def __add__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a+b)


    def __radd__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a+b)

        
    def __sub__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a-b)


    def __rsub__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: b-a)


    def __invert__(self) -> "SParam":
        return SParam(self.name, self.f, 1/self.s, self.z0)

    
    def abs(self) -> "SParam":
        return SParam(self.name, self.f, np.abs(self.s), self.z0)

    
    def db(self) -> "SParam":
        return SParam(self.name, self.f, 20*np.log10(np.maximum(1e-15,np.abs(self.s))), self.z0)

    
    def ml(self) -> "SParam":
        return SParam(self.name + ' ML', self.f, 1-(np.abs(self.s)**2), self.z0)

    
    def phase(self, processing: "str|None" = None) -> "SParam":
        s = self.s
        s = np.angle(s)
        if processing == 'remove_linear':
            s = scipy.signal.detrend(np.unwrap(s), type='linear')
        elif processing == 'unwrap':
            s = np.unwrap(s)
        elif s is not None:
            raise ValueError(f'Invalid processing option "{processing}"')
        return SParam(self.name, self.f, s, self.z0)

    
    def plot(self, label: "str" = None, style: "str" = None):
        if label is None:
            label = self.name
        else:
            label = label.replace('%n', self.name)
        SParam.plot_fn(self.f, self.s, self.z0, label, style)

    
    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParam":
        f_start = -1e99 if f_start is None else f_start
        f_end   = +1e99 if f_end   is None else f_end
        new = [(f,s) for (f,s) in zip(self.f, self.s) if f_start<=f<=f_end]
        if len(new)<1:
            raise Exception('SParam.crop_f(): frequency out of range')
        new_f, new_s = zip(*new)
        return SParam(self.name, new_f, new_s, self.z0)
        
    
    def rl_avg(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParam":
        f_start = f_start if f_start is not None else -1e99
        f_end = f_end if f_end is not None else +1e99
        bodefano = BodeFano(self.f, self.s, f_start, f_end, f_start, f_end)
        f = np.array([bodefano.f_integration_actual_start_hz, bodefano.f_integration_actual_stop_hz])
        s11 = pow(10, bodefano.db_total/20)
        s = np.array([s11, s11])
        return SParam(self.name, f, s, self.z0)

    
    def rl_opt(self, f_integrate_start: "float|None" = None, f_integrate_end: "float|None" = None, f_target_start: "float|None" = None, f_target_end: "float|None" = None) -> "SParam":
        f_integrate_start = f_integrate_start if f_integrate_start is not None else -1e99
        f_integrate_end = f_integrate_end if f_integrate_end is not None else +1e99
        bodefano = BodeFano(self.f, self.s, f_integrate_start, f_integrate_end, f_integrate_start, f_integrate_end)
        f_target_start = f_target_start if f_target_start is not None else bodefano.f_integration_actual_start_hz
        f_target_end = f_target_end if f_target_end is not None else bodefano.f_integration_actual_stop_hz
        bodefano = BodeFano(self.f, self.s, f_integrate_start, f_integrate_end, f_target_start, f_target_end)
        f = np.array([f_target_start, f_target_end])
        s11 = pow(10, bodefano.db_optimized/20)
        s = np.array([s11, s11])
        return SParam(self.name, f, s, self.z0)
    

    def save(self, filename: str):
        
        ext = os.path.splitext(filename)[1].lower()

        s = np.ndarray([len(self.f),1,1], dtype=complex)
        s[:,0,0] = self.s
        nw = skrf.Network(s=s, f=self.f, f_unit='Hz', z0=self.z0, comment=self.name)
        
        if ext=='.cti' or ext=='.citi':
            CitiWriter().write(nw, filename)
        
        elif m := re.match(r'\.s([0-9])+p', ext):
            n = int(m.group(1))
            if n != nw.nports:
                logging.warning(f'Saving {nw.nports}-port into .s{n}p-file.')
            nw.write_touchstone(filename)
        
        elif ext=='.xls' or ext=='.xlsx':
            nw.write_spreadsheet(filename, form='db', file_type='excel')
        
        elif ext=='.csv':
            nw.write_spreadsheet(filename, form='db', file_type='csv')
        
        else:
            raise ValueError(f'Unknown file extension: "{ext}"')

        logging.info(f'Saved parameter <{self.name}> to <{filename}>')
    

    def __repr__(self):
        return f'<SParam("{self.name}", f={self.f}, s={self.s})>'



class SParams:

    def __init__(self, sps: "list[SParam]"):
        self.sps = sps


    def _broadcast(self, sp: "SParams") -> "SParams":
        if isinstance(sp, (int,float,complex,np.ndarray)):
            return [sp] * len(self.sps)
        if not isinstance(sp, SParams):
            raise ValueError('Expected operand of type S-parameters, or numeric')
        if len(sp.sps) == 1:
            return [sp.sps[0]] * len(self.sps)
        elif len(sp.sps) == len(self.sps):
            return self.sps
        raise ValueError(f'Argument has dimension {len(sp.sps)}, but must nave 1 or {len(self.sps)}')
    

    def _unary_op(self, fn, return_sps, **kwargs):
        result = []
        for sp in self.sps:
            try:
                result.append(fn(sp, **kwargs))
            except Exception as ex:
                logging.warning(f'Unary operation <{fn}> on sparam <{sp.name}> failed ({ex}), ignoring')
        if return_sps:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_sps, **kwargs):
        result = []
        for sp,other in zip(self.sps, self._broadcast(others)):
            try:
                result.append(fn(sp, other, **kwargs))
            except Exception as ex:
                logging.warning(f'Binary operation <{fn}> on sparam <{sp.name}> failed ({ex}), ignoring')
        if return_sps:
            return SParams(sps=result)
        else:
            return result

        
    def __truediv__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__truediv__, others, True)


    def __rtruediv__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__rtruediv__, others, True)

        
    def __mul__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__mul__, others, True)


    def __rmul__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__rmul__, others, True)

        
    def __pow__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__pow__, others, True)


    def __rpow__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__rpow__, others, True)
        

    def __add__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__add__, others, True)


    def __radd__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__radd__, others, True)
        

    def __sub__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__sub__, others, True)


    def __rsub__(self, others: "SParams|float") -> "SParams":
        return self._binary_op(SParam.__rsub__, others, True)


    def __invert__(self) -> "SParams":
        return self._unary_op(SParam.__invert__, True)
    

    def abs(self) -> "SParams":
        return self._unary_op(SParam.abs, True)
    

    def db(self) -> "SParams":
        return self._unary_op(SParam.db, True)
    

    def ml(self) -> "SParams":
        return self._unary_op(SParam.ml, True)

    
    def phase(self, processing: "str|None" = None) -> "SParams":
        return self._unary_op(SParam.phase, True, processing=processing)
    

    def plot(self, label: "str|None" = None, style: "str|None" = None):
        self._unary_op(SParam.plot, False, label=label, style=style)
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParams":
        return self._unary_op(SParam.crop_f, True, f_start=f_start, f_end=f_end)
    

    def rl_avg(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParams":
        return self._unary_op(SParam.rl_avg, True, f_start=f_start, f_end=f_end)
    

    def rl_opt(self, f_integrate_start: "float|None" = None, f_integrate_end: "float|None" = None, f_target_start: "float|None" = None, f_target_end: "float|None" = None) -> "SParams":
        return self._unary_op(SParam.rl_opt, True, f_integrate_start=f_integrate_start, f_integrate_end=f_integrate_end, f_target_start=f_target_start, f_target_end=f_target_end)
    

    def save(self, filename: str):
        WILDCARD = '$$'
        
        if len(self.sps) > 1:
            if WILDCARD not in filename:
                raise RuntimeError(f'Please add a wildcard ("{WILDCARD}") to the filename if you want to save multiple parameters.')
        
        for sp in self.sps:
            [directory, name] = os.path.split(filename)
            [name, ext] = os.path.splitext(name)
            name = sanitize_filename(name.replace(WILDCARD, sp.name))
            path = os.path.join(directory, name+ext)
            sp.save(path)
    

    def __repr__(self):
        if len(self.sps) == 1:
            return f'<SParams({self.sps[0]})>'
        return f'<SParams({len(self.sps)}x SParam, 1st is {self.sps[0]})>'
    
    
    def _count(self) -> int:
        return len(self.sps)
