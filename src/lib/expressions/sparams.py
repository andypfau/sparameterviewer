from __future__ import annotations

from ..sparam_file import SParamFile, PathExt
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..utils import sanitize_filename
from ..citi import CitiWriter
from ..settings import Settings
from .helpers import format_call_signature

import skrf, math, os
import numpy as np
import fnmatch
import logging
import scipy.signal, scipy.stats
import os
import re
from typing import Callable



class SParam:


    _plot_fn: Callable[[np.ndarray,np.ndarray,complex,str,str,str,float,PathExt,str], None]


    def __init__(self, name: str, f: np.ndarray, s: np.ndarray, z0: float, original_files: set[PathExt] = None, param_type: str|None=None):
        assert len(f) == len(s), f'Expected frequency and S vecors to have same length, got {len(f)} and {len(s)}'
        self.name, self.f, self.s, self.z0 = name, f, s, z0
        self.original_files, self.param_type = original_files or set(), param_type
    

    def _modified_copy(self, *, name: str|None = None, f: np.ndarray|None = None, s: np.ndarray|None = None, z0: float|None = None, original_files: set[PathExt] = None, param_type: str|None=None) -> SParam:
        return SParam(
            name if name is not None else self.name,
            f if f is not None else self.f,
            s if s is not None else self.s,
            z0 if z0 is not None else self.z0,
            original_files if original_files is not None else self.original_files,
            param_type if param_type is not None else self.param_type
        )
    

    @staticmethod
    def _adapt_f(a: "SParam", b: "SParam") -> "tuple[skrf.Network,skrf.Network]":
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
    def _op(a: "SParam", b: "SParam", op: "Callable", op_type_str: str = '.op.') -> "SParam":
        if isinstance(a, (int,float,complex,np.ndarray)):
            return SParam(b.name, b.f, op(a,np.array(np.ndarray.flatten(b.s))), z0=b.z0, original_files=b.original_files, param_type='const')
        if isinstance(b, (int,float,complex,np.ndarray)):
            return SParam(a.name, a.f, op(np.array(np.ndarray.flatten(a.s)),b), z0=a.z0, original_files=a.original_files, param_type='const')
        a_nw, b_nw = SParam._adapt_f(a, b)
        a_s = np.array(np.ndarray.flatten(a_nw.s))
        b_s = np.array(np.ndarray.flatten(b_nw.s))
        c_s = op(a_s, b_s)
        c_t = a.param_type + op_type_str + b.param_type
        return a._modified_copy(f=a_nw.f, s=c_s, original_files=a.original_files|b.original_files, param_type=c_t)

        
    def __truediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a/b, op_type_str='/')


    def __rtruediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a/b, op_type_str='/')

        
    def __mul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a*b, op_type_str='*')


    def __rmul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a*b, op_type_str='*')

        
    def __pow__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a**b, op_type_str='^')


    def __rpow__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a**b, op_type_str='^')

        
    def __add__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a+b, op_type_str='+')


    def __radd__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a+b, op_type_str='+')

        
    def __sub__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a-b, op_type_str='-')


    def __rsub__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: b-a, op_type_str='-')


    def __invert__(self) -> "SParam":
        return self._modified_copy(s=1/self.s, param_type=self.param_type+'.inv')

    
    def abs(self) -> "SParam":
        return self._modified_copy(s=np.abs(self.s), param_type=self.param_type+'.abs')

    
    def db(self) -> "SParam":
        return self._modified_copy(s=20*np.log10(np.maximum(1e-15,np.abs(self.s))).astype(float), param_type=self.param_type+'.db')

    
    def db10(self) -> "SParam":
        return self._modified_copy(s=10*np.log10(np.maximum(1e-30,np.abs(self.s))).astype(float), param_type=self.param_type+'.db')

    
    def db20(self) -> "SParam":
        return self._modified_copy(s=20*np.log10(np.maximum(1e-15,np.abs(self.s))).astype(float), param_type=self.param_type+'.db')

    
    def ml(self) -> "SParam":
        return self._modified_copy(name=self.name+' ML', s=np.sqrt(1-(np.abs(self.s)**2)).astype(complex), param_type=self.param_type+'.ml')

    
    def vswr(self) -> "SParam":
        return self._modified_copy(name=self.name+' VSWR', s=(1+np.abs(self.s))/(1-np.abs(self.s)).astype(float), param_type=self.param_type+'.vswr')

    
    def phase(self, processing: "str|None" = None) -> "SParam":
        s = self.s
        s = np.angle(s)
        if processing == 'remove_linear':
            s = scipy.signal.detrend(np.unwrap(s), type='linear')
        elif processing == 'unwrap':
            s = np.unwrap(s)
        elif s is not None:
            raise ValueError(f'Invalid processing option "{processing}"')
        return self._modified_copy(s=s.astype(float), param_type=self.param_type+'.pha')


    def norm(self, at_f: float, method='div') -> "SParam":
        idx = np.argmin(np.abs(self.f - at_f))
        ref = self.s[idx]
        s = self.s.copy()
        if method == 'div':
            s = s / ref
        elif method == 'sub':
            s = s - ref
        else:
            raise ValueError(f'Expected method to be "div" or "sub", got "{method}"')
        return self._modified_copy(s=s, name=f'{self.name} norm.', param_type=self.param_type+'.norm')

    
    @staticmethod
    def plot_xy(x: np.ndarray, y: np.ndarray, z0: complex, label: str = None, style: str = None, color: str = None, width: float = None, opacity: float = None, original_files: set[PathExt] = None, param_type: str = None):
        SParam._plot_fn(x, y, z0, label, style, color, width, opacity, original_files, param_type)

    
    def plot(self, label: str = None, style: str = None, color: str = None, width: float = None, opacity: float = None, original_files: set[PathExt] = None, param_type: str = None):
        if label is None:
            label = self.name
        else:
            label = label.replace('$NAME', self.name)
        SParam.plot_xy(self.f, self.s, self.z0, label, style, color, width, opacity, original_files, param_type)

    
    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParam":
        f_start = -1e99 if f_start is None else f_start
        f_end   = +1e99 if f_end   is None else f_end
        new = [(f,s) for (f,s) in zip(self.f, self.s) if f_start<=f<=f_end]
        if len(new)<1:
            raise Exception('SParam.crop_f(): frequency out of range')
        new_f, new_s = zip(*new)
        return self._modified_copy(f=new_f, s=new_s)
        
    
    def rl_avg(self, f_integrate_start: "float|any" = any, f_integrate_end: "float|any" = any, f_target_start: "float|any" = any, f_target_end: "float|any" = any) -> "SParam":
        
        if f_integrate_start is any:
            f_integrate_start = -1e99
        if f_integrate_end is any:
            f_integrate_end = +1e99
        
        if f_target_start is any or f_target_end is any:
            
            bodefano = BodeFano(self.f, self.s, f_integrate_start, f_integrate_end, f_integrate_start, f_integrate_end)

            if f_target_start is any:
                f_target_start = bodefano.f_integration_actual_start_hz
            if f_target_end is any:
                f_target_end = bodefano.f_integration_actual_stop_hz
        
        bodefano = BodeFano(self.f, self.s, f_integrate_start, f_integrate_end, f_target_start, f_target_end)
        s11_linear = pow(10, bodefano.db_achievable/20)

        f = np.array([f_target_start, f_target_end])
        s = np.array([s11_linear, s11_linear])
        return self._modified_copy(f=f, s=s, param_type=self.param_type+'.rlavg')
    
        

    def map(self, fn: "Callable[[np.ndarray],np.ndarray]"):
        s = np.array(fn(self.s))
        if s.shape != self.s.shape:
            raise RuntimeError(f'SParam.map(): user-provided function returned a different shape (expected {self.s.shape}, got {s.shape})')
        return self._modified_copy(name=f'map({self.name})', s=s, param_type=self.param_type+'.map')
    
    
    def rename(self, name: str=None, prefix: str=None, suffix: str=None, pattern: str=None, subs: str=None):
        new_name = self.name
        if name is not None:
            new_name = name
        if prefix is not None:
            new_name = prefix + new_name
        if suffix is not None:
            new_name = new_name + suffix
        if pattern is not None or subs is not None:
            if pattern is None or subs is None:
                raise ValueError('SParam.rename(): pattern and subs must be specified together')
            new_name = re.sub(pattern, subs, new_name)
        return self._modified_copy(name=new_name)
    

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
    
    
    @staticmethod
    def _broadcast(a, b) -> "tuple[list[SParams],list[SParams]]":
        
        assert isinstance(a,SParams) or isinstance(b,SParams), f'Unexpected objects for broadcasting: <{type(a)}> and <{type(b)}> (expected at least one to be SParams)'
        
        if isinstance(a, (int,float,complex,np.ndarray)):
            return [a]*len(b.sps), b.sps
        if isinstance(b, (int,float,complex,np.ndarray)):
            return a.sps, [b]*len(a.sps)
        
        assert isinstance(a,SParams) and isinstance(b,SParams), f'Unexpected objects for broadcasting: <{type(a)}> and <{type(b)}> (expected both to be SParams)'
        
        if len(a.sps) == len(b.sps):
            return a.sps, b.sps
        if len(a.sps) == 1:
            return [a.sps[0]] * len(b.sps), b.sps
        if len(b.sps) == 1:
            return a.sps, [b.sps[0]]*len(a.sps)

        raise ValueError(f'Cannot broadcast SParams of size {len(a.sps)} and {len(b.sps)}')


    def _unary_op(self, fn, return_sps, **kwargs):
        result = []
        for sp in self.sps:
            try:
                result.append(fn(sp, **kwargs))
            except Exception as ex:
                logging.warning(f'Method <{format_call_signature(fn,[],kwargs)}> on sparam <{sp.name}> failed ({ex}), ignoring')
        if return_sps:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_sps, **kwargs):
        result = []
        for sp,other in zip(*SParams._broadcast(self, others)):
            try:
                result.append(fn(sp, other, **kwargs))
            except Exception as ex:
                logging.warning(f'Method <{format_call_signature(fn,[],kwargs)}> on sparam <{sp.name}> failed ({ex}), ignoring')
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
    

    def vswr(self) -> "SParams":
        return self._unary_op(SParam.vswr, True)

    
    def phase(self, processing: "str|None" = None) -> "SParams":
        return self._unary_op(SParam.phase, True, processing=processing)


    def norm(self, at_f: float, method='div') -> "SParams":
        return self._unary_op(SParam.norm, True, at_f=at_f, method=method)

    
    def plot(self, label: "str|None" = None, style: "str|None" = None, color: "str|None" = None, width: "float|None" = None, opacity: "float|None" = None):
        for sp in self.sps:
            try:
                sp.plot(label=label, style=style, color=color, width=width, opacity=opacity, original_files=sp.original_files, param_type=sp.param_type)
            except Exception as ex:
                logging.warning(f'Plotting of <{sp.name}> failed ({ex}), ignoring')
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParams":
        return self._unary_op(SParam.crop_f, True, f_start=f_start, f_end=f_end)


    def _interpolate(self, f: np.ndarray):
        if len(self.sps) < 1:
            return SParams(sps=[])
        result = []
        for sp in self.sps:
            try:
                mag, pha = np.abs(sp.s), np.unwrap(np.angle(sp.s))
                mag_int, pha_int = np.interp(f, sp.f, mag), np.interp(f, sp.f, pha)
                s_int = mag_int * np.exp(1j*pha_int)
                result.append(sp._modified_copy(f=f, s=s_int))
            except Exception as ex:
                logging.warning(f'Interpolating <{sp.name}> failed ({ex}), ignoring')
        return SParams(sps=result)


    def interpolate_lin(self, f_start: float|None = None, f_end: float|None = None, n: int|None = None) -> SParams:
        f_start, f_end, n = self._fill_interpolation_params(f_start, f_end, n)
        assert f_start <= f_end, f'Expected f_start <= f_end, got {f_start} and {f_end}'
        assert n >= 1, f'Expected n >= 1, got {n}'
        return self._interpolate(np.linspace(f_start, f_end, n))


    def interpolate_log(self, f_start: float|None = None, f_end: float|None = None, n: int|None = None) -> SParams:
        f_start, f_end, n = self._fill_interpolation_params(f_start, f_end, n)
        assert f_start > 0, f'Expected f_start > 0, got {f_start}'
        assert f_start <= f_end, f'Expected f_start <= f_end, got {f_start} and {f_end}'
        assert n >= 1, f'Expected n >= 1, got {n}'
        return self._interpolate(np.geomspace(f_start, f_end, n))


    def interpolate(self, f_start: float|None = None, f_end: float|None = None, n: int|None = None) -> SParams:
        return self.interpolate_lin(f_start, f_end, n)


    def _fill_interpolation_params(self, f_start: float|None = None, f_end: float|None = None, n: int|None = None):
        
        if f_start is None or f_end is None:
            all_f = [sp.f for sp in self.sps]
            if f_start is None:
                if len(self.sps)>0:
                    f_start = np.min([np.min(f) for f in all_f])
                else:
                    f_start = 0
            if f_end is None:
                if len(self.sps)>0:
                    f_end = np.max([np.max(f) for f in all_f])
                else:
                    f_end = 0
        
        if n is None:
            if len(self.sps)>0:
                n = max(3, int(round(np.mean([len(f) for f in all_f]))))
            else:
                n = 3
        
        return f_start, f_end, n


    def _interpolated_fn(self, name, fn, min_size=1, type_str: str='.interp', enforce_real: bool=False):
        sps = self.interpolate().sps
        if len(sps) < min_size:
            return SParams(sps=[])
        f = sps[0].f
        
        s_input = []
        list_of_abs = []
        for sp in sps:
            if enforce_real and np.iscomplexobj(sp.s):
                s_input.append(np.abs(sp.s).astype(float))
                list_of_abs.append(sp.name)
            else:
                s_input.append(sp.s)
        if list_of_abs and Settings.verbose:
            logging.debug(f'Took absolute of S-parameters {list_of_abs}')
        s = fn([s for s in s_input])
        return SParams(sps=[SParam(name, f, s, math.nan, param_type=type_str)])


    def mean(self):
        return self._interpolated_fn('Mean', lambda s: np.mean(s,axis=0), type_str='.mean')


    def median(self):
        return self._interpolated_fn('Median', lambda s: np.median(s,axis=0), type_str='.median')


    def sdev(self, ddof=1):
        return self._interpolated_fn('StdDev', lambda s: np.std(s,axis=0,ddof=ddof), min_size=2, type_str='.sdev')


    def rsdev(self, quantiles=50):
        if isinstance(quantiles,(int,float)):
            assert 0<quantiles<100, f'Expected quantile to be in the exlcusive range 0..100%, got {quantiles}'
            q1, q2 = 0.5-(quantiles/100/2), 0.5+(quantiles/100/2)
        elif hasattr(quantiles,'__len__'):
            [qp1, qp2] = quantiles
            assert isinstance(qp1,(int,float)) and isinstance(qp2,(int,float)), f'Expected quantiles to be tuple of percentages'
            assert 0<qp1<100 and 0<qp2<100 and qp1<qp2, f'Expected quantiles to be ascending, and in the exlcusive range 0..100%, got {qp1} and {qp2}'
            q1, q2 = qp1/100, qp2/200
        norm_iqr = scipy.stats.norm.ppf(q2) - scipy.stats.norm.ppf(q1)
        return self._interpolated_fn('RStdDev', lambda s: (np.quantile(s,q2,axis=0)-np.quantile(s,q1,axis=0))/norm_iqr, min_size=2, type_str='.rsdev', enforce_real=True)


    def min(self):
        return self._interpolated_fn('Min', lambda s: np.min(s,axis=0), min_size=1, type_str='.min', enforce_real=True)


    def max(self):
        return self._interpolated_fn('Max', lambda s: np.max(s,axis=0), min_size=1, type_str='.max', enforce_real=True)
    

    def rl_avg(self, f_integrate_start: "float|any" = any, f_integrate_end: "float|any" = any, f_target_start: "float|any" = any, f_target_end: "float|any" = any) -> "SParams":
        return self._unary_op(SParam.rl_avg, True, f_integrate_start=f_integrate_start, f_integrate_end=f_integrate_end, f_target_start=f_target_start, f_target_end=f_target_end)
    

    def map(self, fn: "Callable[[np.ndarray],np.ndarray]"):
        return SParams(sps=[s.map(fn) for s in self.sps])

    
    def rename(self, name: str=None, prefix: str=None, suffix: str=None, pattern: str=None, subs: str=None):
        return self._unary_op(SParam.rename, True, name=name, prefix=prefix, suffix=suffix, pattern=pattern, subs=subs)
    

    def save(self, filename: str):  # TODO: document this command
        WILDCARD_NUM = '$NUM'
        WILDCARD_NAME = '$NAME'

        paths = []
        for i,sp in enumerate(self.sps):
            [dir, name] = os.path.split(filename)
            [name, ext] = os.path.splitext(name)
            name = name.replace(WILDCARD_NUM, str(i+1))
            name = name.replace(WILDCARD_NUM, sp.name)
            name = sanitize_filename(name)
            path = os.path.abspath(os.path.join(dir, name+ext))
            paths.append(path)
        if (len(paths) > 1) and (len(paths) > len(set(paths))):
            raise RuntimeError(f'Filenames are not nunique; please use wildcards ("{WILDCARD_NAME}" or "{WILDCARD_NUM}) in the filename.')
        
        for sp,path in zip(self.sps, path):
            try:
                sp.save(path)
            except Exception as ex:
                logging.error(f'Saving parameter "{sp.name}" to <{path}> failed ({ex})')
    

    def __repr__(self):
        if len(self.sps) == 1:
            return f'<SParams({self.sps[0]})>'
        return f'<SParams({len(self.sps)}x SParam, 1st is {self.sps[0]})>'
    
    
    def _count(self) -> int:
        return len(self.sps)
