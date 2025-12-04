from ..sparam_file import SParamFile, PathExt
from ..bodefano import BodeFano
from ..circles import StabilityCircle, NoiseCircle
from ..sparam_helpers import get_sparam_name, get_port_index, parse_quick_param
from .sparams import SParam, SParams, NumberType
from .helpers import format_call_signature, DefaultAction
from ..utils import sanitize_filename, get_subset, p2db
from ..citi import CitiWriter
from ..si import SiValue
from info import Info

import math
import skrf
import numpy as np
import logging
import re
import os
import logging
from types import NoneType
from typing import overload, Callable



class Network:

    
    def __init__(self, nw: "Network|skrf.Network|SParamFile" = None, name: str = None, original_files: "set[PathExt]" = None):
        self._nw: skrf.Network = None
        self.original_files: set[PathExt] = original_files or set()
        
        if isinstance(nw, SParamFile):
            self._nw = nw.nw
            self.original_files.add(nw.path)
            if name is None:
                name = nw.name
        elif isinstance(nw, Network):
            self._nw = nw._nw
            self.original_files |= nw.original_files
            if name is None:
                name = nw._name
        elif isinstance(nw, skrf.Network):
            self._nw = nw
            if name is None:
                name = nw.name
        elif nw is None:
            pass  # will hopefully be initialized later, when self._calculate() is called
        else:
            raise ValueError(f'Invalid type to init Network object (<{nw}>)')
        
        self._name = name
        
        self._postponed_operations = []
    

    def _ready(self) -> bool:
        return self._name is not None and self._nw is not None


    def _ensure_ready(self) -> bool:
        assert self._ready(), 'Network is not ready'
        self._run_postponed_operations()


    def _run_postponed_operations(self):
        assert self._ready(), 'Network is not ready'

        # swap lists to avoid an infinite recursion...
        operations_to_run, self._postponed_operations = self._postponed_operations, []

        for method, args, kwargs in operations_to_run:
            print(f'~~ Running postponed operation ({method}, {args}, {kwargs})')
            result = method(self, *args, **kwargs)
            self._nw = result._nw
            self._name = result._name
            self.original_files = result.original_files
        

    def _postponable(method):
        def wrapper(self: "Network", *args, **kwargs):
            if self._ready():
                print(f'~~ Running postponable operation immediately ({method}, {args}, {kwargs})')
                return method(self, *args, **kwargs)
            else:
                print(f'~~ Postponing operation ({method}, {args}, {kwargs})')
                import copy
                obj = copy.deepcopy(self)
                obj._postponed_operations.append((method, args, kwargs))
                return obj
        return wrapper

    
    def _calculate(self, f: np.ndarray, z0: float):
        # to be implemented in derived classes; calling this should calculate and update the network (`self.nw`) based on the given frequency and reference impedance
        pass
    
    
    @staticmethod
    def _calculate_with_respect_to(*networks: "Network"):

        f, z0 = None, None
        for network in networks:
            if network._nw is not None:
                f, z0 = network._nw.f, network._nw.z0[0,0]
                break  # TODO: iterate over all networks and find the widest one instead...?
        
        for network in networks:
            network._calculate(f, z0)
    

    @property
    def name(self) -> str:
        self._ensure_ready()
        return self._name
    

    @property
    def nw(self) -> skrf.Network:
        self._ensure_ready()
        return self._nw
    

    @staticmethod
    def _get_adapted_networks(a: "Network", b: "Network") -> "tuple[skrf.Network,skrf.Network]":

        Network._calculate_with_respect_to(a, b)
        
        def crop_ports(a: "skrf.Network", b: "skrf.Network") -> "tuple[skrf.Network,skrf.Network]":
            max_ports = max(a.number_of_ports, b.number_of_ports)
            a.s, b.s = a.s[:,0:max_ports,0:max_ports], b.s[:,0:max_ports,0:max_ports]
            return a, b

        def interpolate_f(a: "skrf.Network", b: "skrf.Network") -> "tuple[skrf.Network,skrf.Network]":
            all_freqs = np.array(sorted(list(set([*a.f, *b.f]))))
            f_new = skrf.Frequency.from_f(all_freqs, unit='Hz')
            assert a.number_of_ports == b.number_of_ports, f'Expected both networks to have the same number of ports during interpolation step, got {a.number_of_ports} and {b.number_of_ports}'
            a_new = Network._get_interpolated_sparams(a.nw, f_new)
            b_new = Network._get_interpolated_sparams(b.nw, f_new)
            return a_new, b_new

        nw_a, nw_b = a.nw.copy(), b.nw.copy()
        if nw_a.number_of_ports != nw_b.number_of_ports:
            nw_a, nw_b = crop_ports(nw_a, nw_b)
        if not np.array_equal(nw_a.f, nw_b.f):
            nw_a, nw_b = interpolate_f(nw_a, nw_b)
        return nw_a, nw_b
    

    @staticmethod
    def _get_interpolated_sparams(nw: skrf.Network, f: np.ndarray) -> skrf.Network:
        
        def interpolate_param(current_s: np.ndarray, current_f: np.ndarray, new_f: np.ndarray) -> np.ndarray:
            current_mag, current_pha = np.abs(current_s), np.unwrap(np.angle(current_s))
            interp_mag = np.interp(new_f, current_f, current_mag)
            interp_pha = np.interp(new_f, current_f, current_pha)
            return interp_mag * np.exp(1j*interp_pha)
        
        s_new = np.ndarray([len(f),nw.nports,nw.nports], dtype=complex)
        for ep in range(nw.nports):
            for ip in range(nw.nports):
                s_new[:,ep,ip] = interpolate_param(nw.s[:,ep,ip], nw.f, f)
        return skrf.Network(s=s_new, name=nw.name, z0=nw.z0, f=f, f_unit='Hz')

    
    def _interpolate(self, f: np.ndarray) -> "Network":
        print(f'Network._interpolate() called')
        return Network(Network._get_interpolated_sparams(self.nw,f), name=self.name, original_files=self.original_files)

        
    def _smatrix_op_smatrix(self, other: "Network|float", operation_fn: Callable, operator_str: str) -> "Network":
        if isinstance(other,int) or isinstance(other,float) or isinstance(other,complex):
            self._calculate(None, None)
            nw = self.nw.copy()
            nw.s = operation_fn(nw.s, other.s)
            return Network(nw, f'{self.name}{operator_str}{other}', original_files=self.original_files)
        elif isinstance(other, Network):
            Network._calculate_with_respect_to(self, other)
            if self.nw.number_of_ports != other.nw.number_of_ports:
                raise RuntimeError(f'The networks "{self.name}" and "{other.name}" have no different number of ports')
            nw, nw2 = Network._get_adapted_networks(self, other)
            nw.s = operation_fn(nw.s, nw2.s)
            return Network(nw, f'{self.name}{operator_str}{other.name}', original_files=self.original_files|other.original_files)
        else:
            raise ValueError(f'Expected operand of type float or Network, got <{other}>')

        
    def __add__(self, other: "Network|float") -> "Network":
        return self._smatrix_op_smatrix(other, lambda s1,s2: s1+s2, '+')

        
    def __sub__(self, other: "Network|float") -> "Network":
        return self._smatrix_op_smatrix(other, lambda s1,s2: s1-s2, '-')

        
    def __matmul__(self, other: "Network") -> "Network":
        return self._smatrix_op_smatrix(other, lambda s1,s2: s1@s2, '@')

        
    def __mul__(self, other: "Network|float") -> "Network":
        return self._smatrix_op_smatrix(other, lambda s1,s2: s1*s2, '*')

        
    def __truediv__(self, other: "Network|float") -> "Network":
        return self._smatrix_op_smatrix(other, lambda s1,s2: s1/s2, '/')


    def __invert__(self) -> "Network":
        return self.invert()


    def __pow__(self, other: "Network") -> "Network":
        a_nw,b_nw = Network._get_adapted_networks(self, other)
        return Network(a_nw**b_nw, self.name+'∘'+other.name, original_files=self.original_files|other.original_files)
    

    def __repr__(self):
        if self._ready():
            return f'<Network({self.nw})>'
        else:
            return f'<Network(...)>'


    def sel_params(self) -> list[SParam]:
        Networks.default_actions_used = True
        params: list[SParam] = []
        unique_param_names = set()
        for action in Networks.default_actions:
            for param in self.s(*action.s_args, **action.s_kwargs):
                if param.param_type not in unique_param_names:
                    params.append(param)
                    unique_param_names.add(param.param_type)
        return params


    def s(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        return self._get_param(egress_port, ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name, param_prefix='S')
    

    def z(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        nw_transformed = self.nw.copy()
        nw_transformed.s = self.nw.z
        obj_transformed = Network(nw_transformed, self.name, original_files=self.original_files)
        return obj_transformed._get_param(egress_port, ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name, param_prefix='Z')
    

    def y(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        nw_transformed = self.nw.copy()
        nw_transformed.s = self.nw.y
        obj_transformed = Network(nw_transformed, self.name, original_files=self.original_files)
        return obj_transformed._get_param(egress_port, ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name, param_prefix='Y')
    

    def abcd(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        nw_transformed = self.nw.copy()
        nw_transformed.s = self.nw.a
        obj_transformed = Network(nw_transformed, self.name, original_files=self.original_files)
        return obj_transformed._get_param(egress_port, ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name, param_prefix='ABCD')
    

    def t(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        nw_transformed = self.nw.copy()
        nw_transformed.s = self.nw.t
        obj_transformed = Network(nw_transformed, self.name, original_files=self.original_files)
        return obj_transformed._get_param(egress_port, ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name, param_prefix='T')
    

    def _get_param(self, egress_port = None, ingress_port = None, *, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None, param_prefix: str) -> list[SParam]:

        result = []
        if not self.nw:
            return result

        ep_filter, ip_filter = None, None
        match (egress_port, ingress_port):
            case int(), None:
                (ep_filter, ip_filter) = parse_quick_param(egress_port)
            case str(), None:
                if m := re.match(r'^([CDS])([CDS])([0-9])?([0-9])$', egress_port.upper()):
                    egress_mode, ingress_mode, egress_mixedport, ingress_mixedport = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
                    ep_filter, ip_filter = get_port_index(self.nw,egress_mode,egress_mixedport)+1, get_port_index(self.nw,ingress_mode,ingress_mixedport)+1
                elif m := re.match(r'^([CDS])([CDS])([0-9]+)[,;]?([0-9]+)$', egress_port.upper()):
                    egress_mode, ingress_mode, egress_mixedport, ingress_mixedport = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
                    ep_filter, ip_filter = get_port_index(self.nw,egress_mode,egress_mixedport)+1, get_port_index(self.nw,ingress_mode,ingress_mixedport)+1
                else:
                    (ep_filter, ip_filter) = parse_quick_param(egress_port)
            case int(), int():
                ep_filter, ip_filter = egress_port, ingress_port
            case int(), any:
                ep_filter = egress_port
            case any, int():
                ip_filter = ingress_port

        for ep in range(1, self.nw.number_of_ports+1):
            for ip in range(1, self.nw.number_of_ports+1):

                if ep_filter is not None and ep!=ep_filter:
                    continue
                if ip_filter is not None and ip!=ip_filter:
                    continue
                if rl_only and ep!=ip:
                    continue
                if il_only and ep==ip:
                    continue
                if fwd_il_only and not (ep>ip):
                    continue
                if rev_il_only and not (ep<ip):
                    continue
                
                param_name = get_sparam_name(self.nw, ep, ip, prefix=param_prefix)
                if name is not None:
                    param_label = name
                else:
                    param_label = param_name
                param_value = self.nw.s[:,ep-1,ip-1].astype(complex)

                result.append(SParam(f'{self.name} {param_label}', self.nw.f, param_value, self.nw.z0[0,ep-1], original_files=self.original_files, param_type=param_name, number_type=NumberType.VectorLike))
        return result
    

    @staticmethod
    def _get_interpolation_frequency(f_start_or_vector_or_reference: "np.ndarray|float|Network", f_stop: float = None, f_step: float = None, n: int = None, scale='lin') -> np.ndarray:
        if isinstance(f_start_or_vector_or_reference, np.ndarray):
            return f_start_or_vector_or_reference
        elif isinstance(f_start_or_vector_or_reference, Network):
            return f_start_or_vector_or_reference.nw.f
        elif isinstance(f_start_or_vector_or_reference, (int,float)):
            if f_stop is None:
                raise ValueError('Interpolate(): f_stop must be provided when first argument is a frequency')
            f_start = f_start_or_vector_or_reference
            if f_step is not None and n is None:
                if scale=='lin':
                    if f_stop < f_start or f_start < 0 or f_step <= 0:
                        raise ValueError('Interpolate(): invalid linear scale')
                    return np.arange(f_start, f_stop, f_step)
                elif scale=='log':
                    if f_stop < f_start or f_start <= 0 or f_step <= 0:
                        raise ValueError('Interpolate(): invlaid logarithmic scale')
                    n = math.ceil(math.log(f_stop/f_start) / math.log(f_step))
                    return np.geomspace(f_start, f_stop, n)
            elif f_step is None and n is not None:
                if scale=='lin':
                    if f_stop < f_start or f_start < 0 or n < 1:
                        raise ValueError('Interpolate(): invalid linear scale')
                    return np.linspace(f_start, f_stop, n)
                elif scale=='log':
                    if f_stop < f_start or f_start <= 0 or n < 1:
                        raise ValueError('Interpolate(): invalid logarithmic scale')
                    return np.geomspace(f_start, f_stop, n)
            raise ValueError('Interpolate(): invalid scale')
        raise ValueError('Interpolate(): invalid argument')
    
    
    def interpolate(self, f_start_or_vector_or_reference: "np.ndarray|float|Network", f_stop: float = None, f_step: float = None, n: int = None, scale='lin')-> "Network":
        print(f'Network.interpolate() called')
        f = Network._get_interpolation_frequency(f_start_or_vector_or_reference=f_start_or_vector_or_reference, f_stop=f_stop, f_step=f_step, n=n, scale=scale)
        return self._interpolate(f)


    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Network":
        f_start = -1e99 if f_start is None else f_start
        f_end   = +1e99 if f_end   is None else f_end
        idx0, idx1 = +1_000_000, -1_000_000
        for idx,f in enumerate(self.nw.f):
            if f>=f_start:
                idx0 = min(idx,idx0)
            if f<=f_end:
                idx1 = max(idx,idx1)
        assert 0<=idx0<len(self.nw.f) and 0<=idx1<len(self.nw.f), f'Expected indices to be within range of network, got {idx0}/{idx1} and length {len(self.nw.f)}'
        if idx0<0 or idx1>=len(self.nw.f):
            raise Exception('Network.crop_f(): frequency out of range')
        new_f = self.nw.f[idx0:idx1+1]
        new_s = self.nw.s[idx0:idx1+1,:,:]
        new_nw = skrf.Network(name=self.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def at_f(self, f: float) -> "Network":
        idx = np.argmin(np.abs(f - self.nw.f))
        new_f = self.nw.f[idx]
        new_s = self.nw.s[idx,:,:]
        new_nw = skrf.Network(name=self.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def at_f(self, f: float) -> "Network":
        idx = np.argmin(np.abs(f - self.nw.f))
        new_f = self.nw.f[idx]
        new_s = self.nw.s[idx,:,:]
        new_nw = skrf.Network(name=self.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)


    @staticmethod
    def _series_to_shunt(s_series: np.ndarray, gamma_term: complex = -1) -> np.ndarray:
        assert s_series.shape[1]==2 and s_series.shape[2]==2
        s11, s21, s12, s22 = s_series[:,0,0], s_series[:,1,0], s_series[:,0,1], s_series[:,1,1]
        
        GAMMA_TEE, LOSS_TEE = -1/3, 2/3  # S-parameters of a tee-junction
        gamma_into_shunted = s11 + s21 * s12 * gamma_term / (1 - s22 * gamma_term)
        gamma_at_tee_leg = gamma_into_shunted / (1 - GAMMA_TEE * gamma_into_shunted)
        
        s_shunt = np.ndarray(s_series.shape, dtype=complex)
        s_shunt[:,0,0] = s_shunt[:,1,1] = GAMMA_TEE + LOSS_TEE**2 * gamma_at_tee_leg
        s_shunt[:,1,0] = s_shunt[:,0,1] = LOSS_TEE + LOSS_TEE**2 * gamma_at_tee_leg

        return s_shunt
        

    @_postponable
    def shunt(self, gamma_term: complex = -1) -> "Network":
        """
        Example usage:
            network.shunt(gamma_term=-1): parallel-circuit a shunt (stub, but shorted at the end)
            network.shunt(gamma_term=+1): parallel-circuit an open stub
            network.shunt(gamma_term=0):  parallel-circuit a terminated stub
        """

        if self.nw.nports != 2:
            raise RuntimeError(f'Network.shunt(): can only shunt a 2-port network')
        
        new_s = Network._series_to_shunt(self.nw.s, gamma_term)

        if gamma_term == -1:  # short
            name_suffix = 'Shunt'
        elif gamma_term == +1:  # open
            name_suffix = 'Stub'
        else:
            name_suffix = 'Term. Stub'
        
        new_nw = skrf.Network(name=f'{self.name} {name_suffix}', f=self.nw.f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def k(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} k', self.nw.f, self.nw.stability, self.nw.z0[0,0], original_files=self.original_files, param_type='k', number_type=NumberType.PlainScalar)
    

    def _delta(self) -> np.ndarray:
        assert self.nw.number_of_ports == 2
        return np.abs(self.nw.s[:,0,0]*self.nw.s[:,1,1] - self.nw.s[:,0,1]*self.nw.s[:,1,0])

    
    def delta(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.delta(mu): cannot calculate determinant of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} Δ', self.nw.f, np.abs(self._delta()), self.nw.z0[0,0], original_files=self.original_files, param_type='Δ', number_type=NumberType.PlainScalar)
    

    def b1(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.b1(): cannot calculate determinant of {self.name} (only valid for 2-port networks)')
        b1 = 1 + np.abs(self.nw.s[:,0,0]) - np.abs(self.nw.s[:,1,1]) - np.abs(self._delta())
        return SParam(f'{self.name} B1', self.nw.f, b1, self.nw.z0[0,0], original_files=self.original_files, param_type='B1', number_type=NumberType.PlainScalar)
    

    def nf(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.nf(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} NF', self.nw.f, p2db(self.nw.nf), self.nw.z0[0,0], original_files=self.original_files, param_type='NF', number_type=NumberType.PlainScalar)
    

    def noisefactor(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.noisefactor(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} F', self.nw.f, self.nw.nf, self.nw.z0[0,0], original_files=self.original_files, param_type='F', number_type=NumberType.MagnitudeLike)
    

    def nf_min(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.nf_min(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} NFmin', self.nw.f, self.nw.nfmin_db, self.nw.z0[0,0], original_files=self.original_files, param_type='NFmin', number_type=NumberType.PlainScalar)
    

    def noisefactor_min(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.noisefactor_min(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} Fmin', self.nw.f, self.nw.nfmin, self.nw.z0[0,0], original_files=self.original_files, param_type='Fmin', number_type=NumberType.MagnitudeLike)
    

    def gamma_opt(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.gamma_opt(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        gamma_opt = (self.nw.z_opt - self.nw.z0[0,0]) / (self.nw.z_opt + self.nw.z0[0,0])
        return SParam(f'{self.name} Γopt', self.nw.f, gamma_opt, self.nw.z0[0,0], original_files=self.original_files, param_type='Γopt', number_type=NumberType.VectorLike)
    

    def z_opt(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.z_opt(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} Zopt', self.nw.f, self.nw.z_opt, self.nw.z0[0,0], original_files=self.original_files, param_type='Zopt', number_type=NumberType.VectorLike)
    

    def rn(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.rn(): cannot determine noise parameters of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} RN', self.nw.f, self.nw.rn, self.nw.z0[0,0], original_files=self.original_files, param_type='RN', number_type=NumberType.PlainScalar)


    def plot_noise(self, db: "float|np.ndarray", f: "float|np.ndarray" = None, n: int = None, n_points=101, label: "str|None" = None, style: "str|None" = None, color: "str|None" = None, width: "float|None" = None, opacity: "float|None" = None):
        
        if not hasattr(db, '__len__'):
            db = [db]
        
        def _plot_noise(db, f):
            nonlocal n_points, label, style, color, width, opacity
            try:
                stab = NoiseCircle(self.nw, f, db)
                data = stab.get_plot_data(n_points)
                freq = np.full([n_points], f)
                final_label = label if label is not None else f'{self.name} NF {db} dB {SiValue(f,"Hz")}'
                SParam.plot_xy(freq, data, self.nw.z0, final_label, style, color, width, opacity, self.original_files, 'noise') 
            except:
                pass  # ignore this, contintue with other circles
        
        if f is not None and n is None:
            if not hasattr(f, '__len__'):
                f = [f]
            for f1 in f:
                for db1 in db:
                    _plot_noise(db1, f1)
        elif f is None:
            n = n if n is not None else 1
            for f1 in get_subset(self.nw.f, n):
                for db1 in db:
                    _plot_noise(db1, f1)
        else:
            raise ValueError('plot_noise(): need either argument f or n')
    

    def mag(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.mag(): cannot calculate maximum available power gain of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} MAG', self.nw.f, self.nw.max_gain, self.nw.z0[0,0], original_files=self.original_files, param_type='MAG', number_type=NumberType.MagnitudeLike)
    

    def msg(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.msg(): cannot calculate maximum stable power gain of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} MSG', self.nw.f, self.nw.max_stable_gain, self.nw.z0[0,0], original_files=self.original_files, param_type='MSG', number_type=NumberType.MagnitudeLike)
    

    def u(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.u(): cannot calculate Mason\'s unilateral gain of {self.name} (only valid for 2-port networks)')
        return SParam(f'{self.name} U', self.nw.f, self.nw.unilateral_gain, self.nw.z0[0,0], original_files=self.original_files, param_type='U', number_type=NumberType.MagnitudeLike)
    

    def mu(self, mu: int = 1):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.mu(mu): cannot calculate stability factor of {self.name} (only valid for 2-port networks)')
        if mu!=1 and mu!=2:
            raise RuntimeError(f'Network.mu(mu): argument mu must be 1 or 2')
        # see https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability
        if mu==1:
            p1,p2 = 0,1
        else:
            p1,p2 = 1,0
        stability_factor = (1 - np.abs(self.nw.s[:,p1,p1]**2)) / (np.abs(self.nw.s[:,p2,p2]-np.conjugate(self.nw.s[:,p1,p1])*self._delta()) + np.abs(self.nw.s[:,1,0]*self.nw.s[:,0,1]))
        return SParam(f'{self.name} µ{mu}', self.nw.f, stability_factor, self.nw.z0[0,0], original_files=self.original_files, param_type=f'µ{mu}', number_type=NumberType.PlainScalar)
    

    def losslessness(self):
        s = self.nw.s
        
        # A network is lossless if S^T x S* = U (see e.g. Pozar, 4.3). This function returns, per frequency,
        #   the highest element of the matrix |S^T ⋅ S * - U|, i.e. if the result is 0, the network is lossless

        st = np.transpose(s, (0,2,1))
        sc = np.conjugate(s)
        prod = np.matmul(st, sc)
        target = np.eye(self.nw.nports)
        errors = np.abs(prod - target)
        result_metric = np.max(errors, axis=(1,2))  # should be zero if lossless
        
        return SParam(f'{self.name} Losslessness', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'losslessness', number_type=NumberType.PlainScalar)
    

    def passivity(self):
        s = self.nw.s
        
        # A network is passive if λ >= 0 for all eigenvalues λ of U - S^H ⋅ S (see <https://ibis.org/summits/nov10b/tseng.pdf> and also
        #   <https://www.simberian.com/Presentations/Shlepnev_S_ParameterQualityMetrics_July2014_final.pdf>)
        # This function returns, per frequency, max(0,λ) of the highest eigenvector λ, i.e. if the result is zero, the network is reciprocal.
        s_h = np.conjugate(np.transpose(s, (0,2,1)))
        prod = np.eye(self.nw.nports) - np.matmul(s_h, s)

        result_metric = np.zeros([len(self.nw.f)], dtype=float)
        for idx in range(len(self.nw.f)):  # for each frequency
            prod_submat = prod[idx,:,:]
            eigenvalues = np.real(np.linalg.eigvals(prod_submat))
            passivity_error = np.maximum(0, -eigenvalues)
            worst_error = np.max(passivity_error)
            result_metric[idx] = worst_error
        
        return SParam(f'{self.name} Passivity', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'passivity', number_type=NumberType.PlainScalar)
    

    def reciprocity(self):
        if self.nw.nports < 2:
            raise RuntimeError(f'Network.reciprocity(): cannot calculate reciprocity of {self.ame} (only valid for 2-port or higher networks)')
        s = self.nw.s
        
        # A network is reciprocal if S^T = S (see e.g. Pozar, 1.9), This function returns, per frequency,
        #   the highest element of the matrix |S^T-S|, i.e. if the result is zero, the network is reciprocal.

        st = np.transpose(s, (0,2,1))
        diff = st - s
        absdiff = np.abs(diff)
        result_metric = np.max(absdiff, axis=(1,2))  # should be zero if reciprocal

        return SParam(f'{self.name} Reciprocity', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'reciprocity', number_type=NumberType.PlainScalar)
    

    def symmetry(self):
        if self.nw.nports < 2:
            raise RuntimeError(f'Network.symmetry(): cannot calculate reciprocity of {self.name} (only valid for 2-port or higher networks)')
        s = self.nw.s
        
        # I define a network as symmetric if it is reciprocal, and additionally Sii=Sjj=Skk..., This function returns, per frequency,
        #   the highest element of the matrix |S^T-S|, plus the highest difference between any diagonal elements; i.e. if the result
        #   is zero, the network is symmetric.

        st = np.transpose(s, (0,2,1))
        diff = st - s
        absdiff = np.abs(diff)
        result_metric_ij = np.max(absdiff, axis=(1,2))  # should be zero if reciprocal

        result_metric_ii = np.zeros([len(self.nw.f)], dtype=float)
        for i in range(self.nw.nports):
            for j in range(self.nw.nports):
                result_metric_ii = np.maximum(result_metric_ii, np.abs(s[:,i,i]-s[:,j,j]))

        result_metric = result_metric_ij + result_metric_ii

        return SParam(f'{self.name} Symmetry', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'symmetry', number_type=NumberType.PlainScalar)
    

    def half(self, method: str = 'IEEE370NZC', side: int = 1) -> "Network":
        if method=='IEEE370NZC':
            from skrf.calibration import IEEEP370_SE_NZC_2xThru # don't import on top of file, as some older versions of the package don't provide this yet
            deembed = IEEEP370_SE_NZC_2xThru(dummy_2xthru=self.nw)
            if side==1:
                return Network(deembed.s_side1, name=self.name+'_side1', original_files=self.original_files)
            elif side==2:
                return Network(deembed.s_side2.flipped(), name=self.name+'_side2', original_files=self.original_files)
            else:
                raise ValueError(f'half(): Invalid side, must be 1 or 2')
        elif method=='ChopInHalf':
            return Network(skrf.network.chopinhalf(self.nw), original_files=self.original_files)
        else:
            raise ValueError(f'half(): Invalid method, must be <IEEE370NZC> or <ChopInHalf>')
    

    def flip(self) -> "Network":
        return Network(skrf.Network(name=self.name, f=self.nw.f, s=skrf.network.flip(self.nw.s), f_unit='Hz'), name='~'+self.name, original_files=self.original_files)
    

    def invert(self) -> "Network":
        return Network(self.nw.inv, name='!'+self.name, original_files=self.original_files)

    
    def add_pr(self, resistance: float, port: int = 1) -> "Network":
        logging.warning('Network.add_pr(): obsolete, use Comp.R().shunt() instead')
        from .components import Components
        if port == 1:
            return Components.RSer(resistance) ** self
        elif port == 2:
            return self ** Components.RShunt(resistance)
        else:
            raise ValueError(f'Invalid port number: {port}')

    
    def add_pl(self, inductance: float, port: int = 1) -> "Network":
        logging.warning('Network.add_pl(): obsolete, use Comp.L().shunt() instead')
        from .components import Components
        if port == 1:
            return Components.LShunt(inductance) ** self
        elif port == 2:
            return self ** Components.LShunt(inductance)
        else:
            raise ValueError(f'Invalid port number: {port}')
    

    def add_pc(self, capacitance: float, port: int = 1) -> "Network":
        logging.warning('Network.add_pc(): obsolete, use Comp.C().shunt() instead')
        from .components import Components
        if port == 1:
            return Components.CShunt(capacitance) ** self
        elif port == 2:
            return self ** Components.CShunt(capacitance)
        else:
            raise ValueError(f'Invalid port number: {port}')


    def plot_stab(self, f: "float|np.ndarray" = None, n: int = None, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None, color: "str|None" = None, width: "float|None" = None, opacity: "float|None" = None):
                
        def _plot_stab(f):
            nonlocal port, n_points, label, style, color, width, opacity
            try:
                stab = StabilityCircle(self.nw, f, port)
                data = stab.get_plot_data(n_points)
                freq = np.full([n_points], f)
                final_label = label if label is not None else f'{self.name} St. {SiValue(f,"Hz")} P{port}'
                final_label += ' (s.i.)' if stab.stable_inside else ' (s.o.)'
                SParam.plot_xy(freq, data, self.nw.z0, final_label, style, color, width, opacity, self.original_files, 'stability')
            except:
                pass  # ignore this, contintue with other circles
        
        if f is not None and n is None:
            if not hasattr(f, '__len__'):
                f = [f]
            for f1 in f:
                _plot_stab(f1)
        elif f is None:
            n = n if n is not None else 1
            for f1 in get_subset(self.nw.f, n):
                _plot_stab(f1)
        else:
            raise ValueError('plot_stab(): need either argument f or n')
        
        
    
    def quick(self, *items):
        for (e,i) in [parse_quick_param(item) for item in items]:
            SParams(self.s(e,i)).plot()
    
    
    def set_modes(self, port_modes: list[str]) -> "Network":
        """
        Interpret the ports of the network as a mixed-mode network.
        Argument <port_modes>: list of modes for each port, e.g.
            ["C","C","D","D"], which means:
            - objects's port 1 is common mode of network's port 1
            - objects's port 2 is common mode of network's port 2
            - objects's port 3 is differential mode of network's port 1
            - objects's port 4 is differential mode of network's port 2
        """

        if len(port_modes) != self.nw.number_of_ports:
            raise ValueError(f'Invalid number of port modes (expected {self.nw.number_of_ports}, got {len(port_modes)})')
        
        for i,mode in enumerate(port_modes):
            mode_uc = mode.upper()
            if mode_uc not in ['S','C','D']:
                raise ValueError(f'Invalid port mode: "{mode}" (expected one of "S", "C", "D")')
            port_modes[i] = mode_uc
        
        new_nw = self.nw.copy()
        new_nw.port_modes = port_modes
        return Network(new_nw, original_files=self.original_files)
    

    def s2m(self, ports: list[str]|str) -> "Network":
        """
        Convert a single-ended network into a mixed-mode network.
        Argument <ports>: list of ports of the single-ended input network, e.g.
            ["P1","P2","N1","N2"], which means:
            - objects's port 1 is positive terminal of network's port 1
            - objects's port 2 is positive terminal of network's port 2
            - objects's port 3 is negative terminal of network's port 1
            - objects's port 4 is negative terminal of network's port 2
        """
        new_nw = self.nw.copy()
        
        if isinstance(ports, str):
            ports = [s.strip() for s in ports.split(',')]
        if len(ports) != self.nw.number_of_ports:
            raise ValueError(f'Invalid number of port definitions (expected {self.nw.number_of_ports}, got {len(ports)})')

        old_indices = []
        for se_port_str in ports:
            try:
                m = re.match(r'^([pn])(\d+)$', se_port_str.lower())
                if not m:
                    raise ValueError()
            except:
                raise ValueError(f'Expecting a list like e.g. ["p1","p2","n1","n2"], got {len(ports)}')
            df_port = int(m.group(2))
            df_index = 2*(df_port-1)
            if m.group(1) == 'n':
                df_index += 1
            # expected order for a 4-port: pos1, neg1, pos2, neg2, ...
            if df_index in old_indices:
                raise ValueError(f'Duplicate port <{se_port_str}>')
            old_indices.append(df_index)
        if len(old_indices) != new_nw.nports:
            raise RuntimeError(f'Unable to change network input terminal order, expected {new_nw.nports} items in list, got {len(old_indices)}')
        new_indices = np.arange(0, new_nw.nports, step=1)
        new_nw.renumber(old_indices, new_indices)

        new_nw.se2gmm(new_nw.nports // 2)
        assert new_nw.nports % 2 == 0, f'Expected number of ports to be an even number, got {new_nw.nports}'
        return Network(new_nw, original_files=self.original_files)
    

    def m2s(self, ports: list[str]|str) -> "Network":
        """
        Convert a mixed-mode network into a single-ended network.
        Argument <ports>: list of ports of the differential input network, e.g.
            ["D","C1","D2","C2"], which means:
            - object's port 1 is differential mode of network's port 1
            - object's port 2 is common mode of network's port 1
            - object's port 3 is differential mode of network's port 2
            - object's port 4 is common mode of network's port 2
        """

        new_nw = self.nw.copy()
        
        if isinstance(ports, str):
            ports = [s.strip() for s in ports.split(',')]
        if len(ports) != self.nw.number_of_ports:
            raise ValueError(f'Invalid number of port definitions (expected {self.nw.number_of_ports}, got {len(ports)})')

        old_indices = []
        for df_port_str in ports:
            try:
                m = re.match(r'^([cd])(\d+)$', df_port_str.lower())
                if not m:
                    raise ValueError()
            except:
                raise ValueError(f'Expecting a list like e.g. ["d1","c1","d2","c2"], got {len(ports)}')
            df_port = int(m.group(2))
            df_index = df_port-1
            if m.group(1) == 'c':
                df_index += new_nw.nports//2
            # expected order for a 4-port: <diff1, diff2, ..., comm1, comm2, ...
            if df_index in old_indices:
                raise ValueError(f'Duplicate port <{df_port_str}>')
            old_indices.append(df_index)
        if len(old_indices) != new_nw.nports:
            raise RuntimeError(f'Unable to change network output terminal order, expected {new_nw.nports} items in list, got {len(old_indices)}')
        new_indices = np.arange(0, new_nw.nports, step=1)
        new_nw.renumber(old_indices, new_indices)

        new_nw.gmm2se(new_nw.nports // 2)
        return Network(new_nw, original_files=self.original_files)


    def renorm(self, z: "complex|list[complex]") -> "Network":
        nw = self.nw.copy()
        nw.renormalize(z)
        return Network(nw, original_files=self.original_files)


    def rewire(self, ports: list[int]) -> "Network":
        nw = self.nw.copy()
        if len(ports) != nw.nports:
            indices_to_keep = [p-1 for p in ports]
            nw_renumbered = nw.subnetwork(indices_to_keep)
        else:
            old_indices = [i for i in range(len(ports))]
            new_indices = [p-1 for p in ports]
            nw_renumbered = nw.renumbered(old_indices, new_indices)
        return Network(nw_renumbered, original_files=self.original_files)


    def save(self, filename: str):
        
        nw = self.nw.copy()
        nw.comments += f'\nExported from {Info.AppName} {Info.AppVersionStr}'
        
        ext = os.path.splitext(filename)[1].lower()
        
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

        logging.info(f'Saved network <{nw.name}> to <{filename}>')



class Networks:
    

    available_networks: "list[skrf.Network]"

    default_actions: "list[DefaultAction]" = []
    default_actions_used: bool = False


    def __init__(self, nws: "list[skrf.Network]|list[Network]|list[SParamFile]" = None):
        def cast(obj):
            if isinstance(obj, Network):
                return obj
            elif isinstance(obj, SParamFile):
                return Network(obj)
            elif isinstance(obj, skrf.Network):
                return Network(obj)
            else:
                raise ValueError(f'Internal error: Network object initiliazed with invalid object ({obj})')
        self.nws = [cast(nw) for nw in nws]


    def _calculate(self, f: np.ndarray, z0: float):
        for nw in self.nws:
            nw._calculate(f, z0)
    

    @staticmethod
    def _broadcast(a, b) -> "tuple[list[Network],list[Network]]":
        
        assert isinstance(a,Networks) or isinstance(b,Networks), f'Unexpected objects for broadcasting: <{type(a)}> and <{type(b)}> (expected at least one to be Networks)'
        
        if isinstance(a, (int,float,complex,np.ndarray)):
            return [a]*len(b.nws), b.nws
        if isinstance(b, (int,float,complex,np.ndarray)):
            return a.nws, [a]*len(a.nws)
        
        assert isinstance(a,Networks) and isinstance(b,Networks), f'Unexpected objects for broadcasting: <{type(a)}> and <{type(b)}> (expected both to be Networks)'
        
        if len(a.nws) == len(b.nws):
            return a.nws, b.nws
        if len(a.nws) == 1:
            return [a.nws[0]] * len(b.nws), b.nws
        if len(b.nws) == 1:
            return a.nws, [b.nws[0]]*len(a.nws)

        raise ValueError(f'Cannot broadcast Networks of size {len(a.nws)} and {len(b.nws)}')


    def _unary_op(self, fn, return_type, *args, **kwargs):
        result = []
        for nw in self.nws:
            try:
                r = fn(nw, *args, **kwargs)
                if hasattr(r, '__len__'):
                    result.extend(r)
                else:
                    result.append(r)
            except Exception as ex:
                logging.warning(f'Method <{format_call_signature(fn,*args,**kwargs)})> on {nw} failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_type, *args, **kwargs):
        result = []
        for nw,other in zip(*Networks._broadcast(self, others)):
            try:
                r = fn(nw, other, *args, **kwargs)
                if hasattr(r, '__len__'):
                    result.extend(r)
                else:
                    result.append(r)
            except Exception as ex:
                logging.warning(f'Method <{format_call_signature(fn,args,kwargs)}> on {nw} failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def __add__(self, other: "Networks|float") -> "Networks":
        return self._binary_op(Network.__add__, other, Networks)


    def __sub__(self, other: "Networks|float") -> "Networks":
        return self._binary_op(Network.__sub__, other, Networks)


    def __matmul__(self, other: "Networks") -> "Networks":
        return self._binary_op(Network.__matmul__, other, Networks)


    def __mul__(self, other: "Networks|float") -> "Networks":
        return self._binary_op(Network.__mul__, other, Networks)


    def __truediv__(self, other: "Networks|float") -> "Networks":
        return self._binary_op(Network.__truediv__, other, Networks)


    def __invert__(self) -> "Networks":
        return self._unary_op(Network.__invert__, Networks)


    def __pow__(self, other: "Networks") -> "Networks":
        return self._binary_op(Network.__pow__, other, Networks)
    

    def __repr__(self):
        if len(self.nws) == 1:
            return f'<Networks({self.nws[0]})>'
        elif len(self.nws) > 1:
            return f'<Networks({len(self.nws)}x Network, 1st is {self.nws[0]})>'
        else:
            return '<Networks(empty)>'
    

    def sel_params(self) -> SParams:
        return self._unary_op(Network.sel_params, SParams)


    def s(self, egress_port = None, ingress_port = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.s, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    

    def z(self, egress_port = None, ingress_port = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.z, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    

    def y(self, egress_port = None, ingress_port = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.y, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    

    def t(self, egress_port = None, ingress_port = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.t, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    

    def abcd(self, egress_port = None, ingress_port = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.abcd, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    
    
    def interpolate(self, f_start_or_vector_or_reference: "np.ndarray|float", f_stop: float = None, f_step: float = None, n: int = None, scale='lin', **kwargs)-> "Networks":
        return self._unary_op(Network.interpolate, Networks, f_start_or_vector_or_reference=f_start_or_vector_or_reference, f_stop=f_stop, f_step=f_step, n=n, scale=scale, **kwargs)


    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks":
        return self._unary_op(Network.crop_f, Networks, f_start=f_start, f_end=f_end)
    

    def at_f(self, f: float) -> "Networks":
        return self._unary_op(Network.at_f, Networks, f=f)

    
    def shunt(self, gamma_term: complex = -1) -> "Networks":
        return self._unary_op(Network.shunt, Networks, gamma_term=gamma_term)
    

    def k(self):
        return self._unary_op(Network.k, SParams)
        
    
    def delta(self):
        return self._unary_op(Network.delta, SParams)
        
    
    def b1(self):
        return self._unary_op(Network.b1, SParams)
        
    
    def mu(self, mu: int = 1):
        return self._unary_op(Network.mu, SParams, mu=mu)
    

    def plot_stab(self, f: "float|np.ndarray" = None, n: int = None, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        self._unary_op(Network.plot_stab, None, f=f, n=n, port=port, n_points=n_points, label=label, style=style)
        
    
    def nf(self):
        return self._unary_op(Network.nf, SParams)
        
    
    def noisefactor(self):
        return self._unary_op(Network.noisefactor, SParams)
        
    
    def nf_min(self):
        return self._unary_op(Network.nf_min, SParams)
        
    
    def noisefactor_min(self):
        return self._unary_op(Network.noisefactor_min, SParams)
        
    
    def gamma_opt(self):
        return self._unary_op(Network.gamma_opt, SParams)
        
    
    def z_opt(self):
        return self._unary_op(Network.z_opt, SParams)
        
    
    def rn(self):
        return self._unary_op(Network.rn, SParams)
    

    def plot_noise(self, db: "float|np.ndarray", f: "float|np.ndarray" = None, n: int = None, n_points=101, label: "str|None" = None, style: "str|None" = None):
        self._unary_op(Network.plot_noise, None, db=db, f=f, n=n, n_points=n_points, label=label, style=style)
    

    # TODO: constant-gain circles

    
    def mag(self):
        return self._unary_op(Network.mag, SParams)
    
    
    def msg(self):
        return self._unary_op(Network.msg, SParams)
    
    
    def u(self):
        return self._unary_op(Network.u, SParams)

    
    def passivity(self):
        return self._unary_op(Network.passivity, SParams)
        
    
    def losslessness(self):
        return self._unary_op(Network.losslessness, SParams)
    

    def reciprocity(self):
        return self._unary_op(Network.reciprocity, SParams)
    

    def symmetry(self):
        return self._unary_op(Network.symmetry, SParams)
    

    def half(self, method: str = 'IEEE370NZC', side: int = 1) -> "Networks":
        return self._unary_op(Network.half, Networks, method=method, side=side)

    
    def flip(self) -> "Networks":
        return self._unary_op(Network.flip, Networks)
    

    def invert(self) -> "Networks":
        return self._unary_op(Network.invert, Networks)

    
    def add_sr(self, resistance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_sr(): obsolete, use Comp.R() instead')
        from .components import Components
        if port == 1:
            return Components.RSer(resistance) ** self
        elif port == 2:
            return self ** Components.RSer(resistance)
        else:
            raise ValueError(f'Invalid port number: {port}')


    def add_sl(self, inductance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_sl(): obsolete, use Comp.L() instead')
        from .components import Components
        if port == 1:
            return Components.LSer(inductance) ** self
        elif port == 2:
            return self ** Components.LSer(inductance)
        else:
            raise ValueError(f'Invalid port number: {port}')

    
    def add_sc(self, capacitance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_sc(): obsolete, use Comp.C() instead')
        from .components import Components
        if port == 1:
            return Components.CSer(capacitance) ** self
        elif port == 2:
            return self ** Components.CSer(capacitance)
        else:
            raise ValueError(f'Invalid port number: {port}')
        
    
    def add_pr(self, resistance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_pr(): obsolete, use Comp.R() instead')
        from .components import Components
        if port == 1:
            return Components.RShunt(resistance) ** self
        elif port == 2:
            return self ** Components.RShunt(resistance)
        else:
            raise ValueError(f'Invalid port number: {port}')
        
    
    def add_pl(self, inductance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_pl(): obsolete, use Comp.L() instead')
        from .components import Components
        if port == 1:
            return Components.LShunt(inductance) ** self
        elif port == 2:
            return self ** Components.LShunt(inductance)
        else:
            raise ValueError(f'Invalid port number: {port}')
        
    
    def add_pc(self, capacitance: float, port: int = 1) -> "Networks":
        logging.warning('Networks.add_pc(): obsolete, use Comp.C() instead')
        from .components import Components
        if port == 1:
            return Components.CShunt(capacitance) ** self
        elif port == 2:
            return self ** Components.CShunt(capacitance)
        else:
            raise ValueError(f'Invalid port number: {port}')
        
    
    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss_db: float = 0, port: int = 1) -> "Network":
        logging.warning('Networks.add_tl(): obsolete, use Comp.Line() instead')
        from .components import Components
        if port == 1:
            return Components.Line(deg=degrees,z=z0,at_f=frequency_hz,db=loss_db) ** self
        elif port == 2:
            return self ** Components.Line(deg=degrees,z=z0,at_f=frequency_hz,db=loss_db)
        else:
            raise ValueError(f'Invalid port number: {port}')
    

    def add_ltl(self, len_m: float, eps_r: float, z0: float = None, db_m_mhz: float = 0, db_m_sqmhz: float = 0, port: int = 1) -> "Network":
        logging.warning('Networks.add_ltl(): obsolete, use Comp.Line() instead')
        from .components import Components
        if port == 1:
            return Components.Line(len=len_m,z=z0,eps_r=eps_r,db_m_mhz=db_m_mhz,db_m_sqmhz=db_m_sqmhz) ** self
        elif port == 2:
            return self ** Components.Line(len=len_m,z=z0,eps_r=eps_r,db_m_mhz=db_m_mhz,db_m_sqmhz=db_m_sqmhz)
        else:
            raise ValueError(f'Invalid port number: {port}')


    def plot_sel_params(self) -> None:
        Networks.default_actions_used = True
        for action in Networks.default_actions:
            self.s(*action.s_args, **action.s_kwargs).plot(*action.plot_args, **action.plot_kwargs)


    def quick(self, *items) -> None:
        self._unary_op(Network.quick, None, *items)
        
    
    def set_modes(self, port_modes: list[str]) -> "Networks":
        return self._unary_op(Network.set_modes, Networks, port_modes=port_modes)
        
    
    def m2s(self, ports: list[str]|str) -> "Networks":
        return self._unary_op(Network.m2s, Networks, ports=ports)
        
    
    def s2m(self, ports: list[str]|str) -> "Networks":
        return self._unary_op(Network.s2m, Networks, ports=ports)
    

    def renorm(self, z: "complex|list[complex]") -> "Networks":
        return self._unary_op(Network.renorm, Networks, z=z)


    def rewire(self, ports: list[int]) -> "Networks":
        return self._unary_op(Network.rewire, Networks, ports=ports)


    def save(self, filename: str):  # TODO: document this command
        WILDCARD_NUM = '$NUM'
        WILDCARD_NAME = '$NAME'

        paths = []
        for i,nw in enumerate(self.nws):
            [dir, name] = os.path.split(filename)
            [name, ext] = os.path.splitext(name)
            name = name.replace(WILDCARD_NUM, str(i+1))
            name = name.replace(WILDCARD_NUM, nw.name)
            name = sanitize_filename(name)
            path = os.path.abspath(os.path.join(dir, name+ext))
            paths.append(path)
        if (len(paths) > 1) and (len(paths) > len(set(paths))):
            raise RuntimeError(f'Filenames are not nunique; please use wildcards ("{WILDCARD_NAME}" or "{WILDCARD_NUM}) in the filename.')
        
        for nw,path in zip(self.nws, path):
            try:
                nw.save(path)
            except Exception as ex:
                logging.error(f'Saving network "{nw.name}" to <{path}> failed ({ex})')


    def _count(self) -> int:
        return len(self.nws)
