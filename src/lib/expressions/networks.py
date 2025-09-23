from ..sparam_file import SParamFile, PathExt
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..sparam_helpers import get_sparam_name, get_port_index, parse_quick_param
from .sparams import SParam, SParams
from .helpers import format_call_signature, DefaultAction
from ..utils import sanitize_filename
from ..citi import CitiWriter
from info import Info

import math
import skrf
import numpy as np
import logging
import re
import os
from types import NoneType
from typing import overload, Callable



class Network:

    
    def __init__(self, nw: "Network|skrf.Network|SParamFile" = None, name: str = None, original_files: "set[PathExt]" = None):
        self.nw: skrf.Network
        self.original_files: set[PathExt] = original_files or set()
        if isinstance(nw, SParamFile):
            self.nw = nw.nw
            self.original_files.add(nw.path)
        elif isinstance(nw, Network):
            self.nw = nw.nw
            self.original_files |= nw.original_files
        elif isinstance(nw, skrf.Network):
            self.nw = nw
        else:
            raise ValueError(f'Invalid type to init Network object (<{nw}>)')
        if name is not None:
            self.nw.name = name
    

    @property
    def name(self):
        return self.nw.name
    

    @staticmethod
    def _get_adapted_networks(a: "Network", b: "Network") -> "tuple[skrf.Network,skrf.Network]":
        
        def crop_ports(a: "skrf.Network", b: "skrf.Network") -> "tuple[skrf.Network,skrf.Network]":
            max_ports = max(a.number_of_ports, b.number_of_ports)
            a.s, b.s = a.s[:,0:max_ports,0:max_ports], b.s[:,0:max_ports,0:max_ports]
            return a, b

        def interpolate_f(a: "skrf.Network", b: "skrf.Network") -> "tuple[skrf.Network,skrf.Network]":
            def interpolate_param(current_s: np.ndarray, current_f: np.ndarray, new_f: np.ndarray) -> np.ndarray:
                current_mag, current_pha = np.abs(current_s), np.unwrap(np.angle(current_s))
                interp_mag = np.interp(new_f, current_f, current_mag)
                interp_pha = np.interp(new_f, current_f, current_pha)
                return interp_mag * np.exp(1j*interp_pha)
            all_freqs = np.array(sorted(list(set([*a.f, *b.f]))))
            f_new = skrf.Frequency.from_f(all_freqs, unit='Hz')
            assert a.number_of_ports == b.number_of_ports, f'Expected both networks to have the same number of ports during interpolation step, got {a.number_of_ports} and {b.number_of_ports}'
            a_s_new = np.ndarray([len(all_freqs), a.number_of_ports, a.number_of_ports], dtype=complex)
            b_s_new = np.ndarray([len(all_freqs), a.number_of_ports, a.number_of_ports], dtype=complex)
            for ep in range(a.number_of_ports):
                for ip in range(a.number_of_ports):
                    a_s_new[:,ep,ip] = interpolate_param(a.s[:,ep,ip], np.array(a.f), all_freqs)
                    b_s_new[:,ep,ip] = interpolate_param(b.s[:,ep,ip], np.array(b.f), all_freqs)
            a_new, b_new = skrf.Network(), skrf.Network()
            a_new.frequency, a_new.s, a_new.z0, a_new.name = f_new, a_s_new, a.z0[0,:a.number_of_ports], a.name
            b_new.frequency, b_new.s, a_new.z0, b_new.name = f_new, b_s_new, a.z0[0,:b.number_of_ports], b.name
            return a_new, b_new

        nw_a, nw_b = a.nw.copy(), b.nw.copy()
        if nw_a.number_of_ports != nw_b.number_of_ports:
            nw_a, nw_b = crop_ports(nw_a, nw_b)
        if not np.array_equal(nw_a.f, nw_b.f):
            nw_a, nw_b = interpolate_f(nw_a, nw_b)
        return nw_a, nw_b

        
    def _smatrix_op_smatrix(self, other: "Network|float", operation_fn: Callable, operator_str: str) -> "Network":
        if isinstance(other,int) or isinstance(other,float) or isinstance(other,complex):
            nw = self.nw.copy()
            nw.s = operation_fn(nw.s, other.s)
            return Network(nw, f'{self.nw.name}{operator_str}{other}', original_files=self.original_files)
        elif isinstance(other, Network):
            if self.nw.number_of_ports != other.nw.number_of_ports:
                raise RuntimeError(f'The networks "{self.nw.name}" and "{other.nw.name}" have no different number of ports')
            nw, nw2 = Network._get_adapted_networks(self, other)
            nw.s = operation_fn(nw.s, nw2.s)
            return Network(nw, f'{self.nw.name}{operator_str}{other.nw.name}', original_files=self.original_files|other.original_files)
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
        # TODO: I have no idea what I was thinking here... why the "+" in the name? Why take the power of two networks?
        # I think I should make this the same way as the implementation of __mul__ and __truediv__, and perhaps add __add__ and __sub__
        a_nw,b_nw = Network._get_adapted_networks(self, other)
        return Network(a_nw**b_nw, a_nw.name+'+'+b_nw.name, original_files=self.original_files|other.original_files)
    

    def __repr__(self):
        return f'<Network({self.nw})>'


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

                result.append(SParam(f'{self.nw.name} {param_label}', self.nw.f, param_value, self.nw.z0[0,ep-1], original_files=self.original_files, param_type=param_name))
        return result
    

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
        new_nw = skrf.Network(name=self.nw.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def at_f(self, f: float) -> "Network":
        idx = np.argmin(np.abs(f - self.nw.f))
        new_f = self.nw.f[idx]
        new_s = self.nw.s[idx,:,:]
        new_nw = skrf.Network(name=self.nw.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def at_f(self, f: float) -> "Network":
        idx = np.argmin(np.abs(f - self.nw.f))
        new_f = self.nw.f[idx]
        new_s = self.nw.s[idx,:,:]
        new_nw = skrf.Network(name=self.nw.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw, original_files=self.original_files)
    

    def k(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.nw.name} (only valid for 2-port networks)')
        return SParam(f'{self.nw.name} k', self.nw.f, self.nw.stability, self.nw.z0[0,0], original_files=self.original_files, param_type='k')
    

    def mu(self, mu: int = 1):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.mu(mu): cannot calculate stability factor of {self.nw.name} (only valid for 2-port networks)')
        if mu!=1 and mu!=2:
            raise RuntimeError(f'Network.mu(mu): argument mu must be 1 or 2')
        # see https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability
        if mu==1:
            p1,p2 = 0,1
        else:
            p1,p2 = 1,0
        delta = self.nw.s[:,0,0]*self.nw.s[:,1,1] - self.nw.s[:,0,1]*self.nw.s[:,1,0]
        stability_factor = (1 - np.abs(self.nw.s[:,p1,p1]**2)) / (np.abs(self.nw.s[:,p2,p2]-np.conjugate(self.nw.s[:,p1,p1])*delta) + np.abs(self.nw.s[:,1,0]*self.nw.s[:,0,1]))
        return SParam(f'{self.nw.name} µ{mu}', self.nw.f, stability_factor, self.nw.z0[0,0], original_files=self.original_files, param_type=f'µ{mu}')
    

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
        
        return SParam(f'{self.nw.name} Losslessness', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'losslessness')
    

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
        
        return SParam(f'{self.nw.name} Passivity', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'passivity')
    

    def reciprocity(self):
        if self.nw.nports < 2:
            raise RuntimeError(f'Network.reciprocity(): cannot calculate reciprocity of {self.nw.name} (only valid for 2-port or higher networks)')
        s = self.nw.s
        
        # A network is reciprocal if S^T = S (see e.g. Pozar, 1.9), This function returns, per frequency,
        #   the highest element of the matrix |S^T-S|, i.e. if the result is zero, the network is reciprocal.

        st = np.transpose(s, (0,2,1))
        diff = st - s
        absdiff = np.abs(diff)
        result_metric = np.max(absdiff, axis=(1,2))  # should be zero if reciprocal

        return SParam(f'{self.nw.name} Reciprocity', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'reciprocity')
    

    def symmetry(self):
        if self.nw.nports < 2:
            raise RuntimeError(f'Network.symmetry(): cannot calculate reciprocity of {self.nw.name} (only valid for 2-port or higher networks)')
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

        return SParam(f'{self.nw.name} Symmetry', self.nw.f, result_metric, self.nw.z0[0,0], original_files=self.original_files, param_type=f'symmetry')
    

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
        return Network(skrf.Network(name=self.nw.name, f=self.nw.f, s=skrf.network.flip(self.nw.s), f_unit='Hz'), name='~'+self.name, original_files=self.original_files)
    

    def invert(self) -> "Network":
        return Network(self.nw.inv, name='!'+self.name, original_files=self.original_files)


    def _get_added_2port(self, s_matrix: np.ndarray, port: int) -> "Network":
        
        if port<1 or port>self.nw.number_of_ports:
            raise ValueError(f'Port number {port} out of range')
        
        if self.nw.number_of_ports==1:
            s_new = np.zeros([len(self.nw.f),1,1], dtype=complex)
            s11 = s_matrix[:,0,0]
            s22 = s_matrix[:,1,1]
            s21 = s_matrix[:,1,0]
            s12 = s_matrix[:,0,1]
            s11_self = self.nw.s[:,0,0]
            delta = 1 - s22 * s11_self
            s_new[:,0,0] = (s11*delta + s21*s11_self*s12) / delta
            return Network(skrf.Network(name=self.nw.name, f=self.nw.f, s=s_new, f_unit='Hz'), original_files=self.original_files)

        elif self.nw.number_of_ports==2:
            other_nw = skrf.Network(name=self.nw.name, f=self.nw.f, s=s_matrix, f_unit='Hz')
            if port==1:
                new_nw = other_nw ** self.nw
            elif port==2:
                new_nw = self.nw ** other_nw
            else:
                raise ValueError()
            return Network(new_nw, original_files=self.original_files)
        else:
            raise RuntimeError('Impedance adding is only supported for 1-port and 2-port networks')
    

    def _get_added_z(self, z: np.ndarray, port: int, mode: str) -> "Network":
        z0 = self.nw.z0[0,0]
        # see https://www.edn.com/bypass-capacitor-s-parameter-models-what-you-need-to-know/
        s_matrix = np.zeros([len(self.nw.f),2,2], dtype=complex)
        if mode=='series':
            factor = 1/(z+2*z0)
            s_matrix[:,0,0] = s_matrix[:,1,1] = z*factor
            s_matrix[:,1,0] = s_matrix[:,0,1] = 2*z0*factor
        elif mode=='parallel':
            factor = 1/(1/z+2/z0)
            s_matrix[:,0,0] = s_matrix[:,1,1] = (1/z)*factor
            s_matrix[:,1,0] = s_matrix[:,0,1] = (2/z0)*factor
        else:
            raise RuntimeError('Invalid Z mode')
        return self._get_added_2port(s_matrix, port)

    
    def add_sr(self, resistance: float, port: int = 1) -> "Network":
        return self._get_added_z(np.full([len(self.nw.f)], resistance), port, 'series')

    
    def add_sl(self, inductance: float, port: int = 1) -> "Network":
        return self._get_added_z(1j*math.tau*self.nw.f*inductance, port, 'series')

    
    def add_sc(self, capacitance: float, port: int = 1) -> "Network":
        return self._get_added_z(1/(1j*math.tau*self.nw.f*capacitance), port, 'series')

    
    def add_pr(self, resistance: float, port: int = 1) -> "Network":
        return self._get_added_z(np.full([len(self.nw.f)], resistance), port, 'parallel')

    
    def add_pl(self, inductance: float, port: int = 1) -> "Network":
        return self._get_added_z(1j*math.tau*self.nw.f*inductance, port, 'parallel')
    

    def add_pc(self, capacitance: float, port: int = 1) -> "Network":
        return self._get_added_z(1/(1j*math.tau*self.nw.f*capacitance), port, 'parallel')
    

    @staticmethod
    def _tline(arg, z0_line, z0_system) -> np.ndarray:
        s_matrix = np.zeros([len(arg),2,2], dtype=complex)
        
        # see https://cds.cern.ch/record/1415639/files/p67.pdf
        sh = np.sinh(arg)
        ch = np.cosh(arg)
        zzpzz = z0_system*z0_system + z0_line*z0_line
        zzmzz = z0_system*z0_system - z0_line*z0_line
        ds = 2*z0_system*z0_line*ch + zzpzz*sh
        s_matrix[:,0,0] = s_matrix[:,1,1] = (zzmzz*sh)/ds
        s_matrix[:,1,0] = s_matrix[:,0,1] = (2*z0_system*z0_line)/ds

        return s_matrix
    

    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss_db: float = 0, port: int = 1) -> "Network":
        """
        Add ideal transmission line to the network
        Arguments:
            degrees:      phase shift of the transmission line, in degrees, at a given frequency (see next argument)
            frequency_hz: the frequency at which the phase shift is defined
            loss_db:      loss of the tranmission line, in dB; loss is frequency-independent
            port:         at which end of the network to add this transmission line
        """
        
        # complex argument for simple transmission line
        loss_v = pow(10, loss_db/20) # dB to volts
        arg_mag = math.log(loss_v) # compensate for the exp-function in the tline equation
        arg_pha = math.radians(degrees) * (self.nw.f/frequency_hz)

        z0_system = self.nw.z0[0,0]
        z0_line = z0 if z0 is not None else z0_system
        s_matrix = Network._tline(1j*arg_pha+arg_mag, z0_line, z0_system)
        return self._get_added_2port(s_matrix, port)
    

    def add_ltl(self, len_m: float, eps_r: float, z0: float = None, db_m_mhz: float = 0, db_m_sqmhz: float = 0, port: int = 1) -> "Network":
        """
        Add lossy transmission line to the network
        Arguments:
            eps_r:     dielectric constant of transmission line material
            z0:        wave impedance of the transmission line
            db_m_mhz:  loss of the tranmission line, in dB/(m*MHz)
            db_m_sqmhz: loss of the tranmission line, in dB/(m*√MHz)
            port:      at which end of the network to add this transmission line
        """
        
        # complex argument for lossy transmission line; see Pozar, Microwave Engineering, sections 2.7 (tlines) and 4.4 (ABCD-params of tlines)
        loss_db = db_m_mhz*(self.nw.f/1e6)*len_m + db_m_sqmhz*np.sqrt(self.nw.f/1e6)*len_m
        loss_v = pow(10, loss_db/20) # dB to volts
        arg_mag = np.log(loss_v) # compensate for the exp-function in the tline equation
        C0 = 299792458
        c_in_dielectric = C0 / math.sqrt(eps_r)
        l = len_m * self.nw.f / c_in_dielectric
        arg_pha = l * math.tau

        z0_system = self.nw.z0[0,0]
        z0_line = z0 if z0 is not None else z0_system
        s_matrix = Network._tline(1j*arg_pha+arg_mag, z0_line, z0_system)
        return self._get_added_2port(s_matrix, port)

    
    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None, color: "str|None" = None, width: "float|None" = None, opacity: "float|None" = None):
        stab = StabilityCircle(self.nw, frequency_hz, port)
        data = stab.get_plot_data(n_points)
        freq = np.full([n_points], frequency_hz)
        label = label if label is not None else self.nw.name
        label += f' (s.i.)' if stab.stable_inside else f' (s.o.)'
        SParam.plot_xy(freq, data, self.nw.z0, label, style, color, width, opacity, self.original_files, 'stability')
        
    
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


    def __init__(self, nws: "list[skrf.Network]|list[Network]" = None):
        self.nws = [Network(nw) for nw in nws]


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
                logging.warning(f'Method <{format_call_signature(fn,*args,**kwargs)})> on network <{nw.nw.name}> failed ({ex}), ignoring')
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
                logging.warning(f'Method <{format_call_signature(fn,args,kwargs)}> on network <{nw.name}> failed ({ex}), ignoring')
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
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks":
        return self._unary_op(Network.crop_f, Networks, f_start=f_start, f_end=f_end)
    

    def at_f(self, f: float) -> "Networks":
        return self._unary_op(Network.at_f, Networks, f=f)
    

    def k(self):
        return self._unary_op(Network.k, SParams)
        
    
    def mu(self, mu: int = 1):
        return self._unary_op(Network.mu, SParams, mu=mu)
        
    
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
        return self._unary_op(Network.add_sr, Networks, resistance=resistance, port=port)


    def add_sl(self, inductance: float, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_sl, Networks, inductance=inductance, port=port)

    
    def add_sc(self, capacitance: float, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_sc, Networks, capacitance=capacitance, port=port)
        
    
    def add_pr(self, resistance: float, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_pr, Networks, resistance=resistance, port=port)
        
    
    def add_pl(self, inductance: float, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_pl, Networks, inductance=inductance, port=port)
        
    
    def add_pc(self, capacitance: float, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_pc, Networks, capacitance=capacitance, port=port)
        
    
    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss_db: float = 0, port: int = 1) -> "Network":
        return self._unary_op(Network.add_tl, Networks, degrees=degrees, frequency_hz=frequency_hz, z0=z0, loss_db=loss_db, port=port)
    

    def add_ltl(self, len_m: float, eps_r: float, z0: float = None, db_m_mhz: float = 0, db_m_sqmhz: float = 0, port: int = 1) -> "Network":
        return self._unary_op(Network.add_ltl, Networks, len_m=len_m, eps_r=eps_r, z0=z0, db_m_mhz=db_m_mhz, db_m_sqmhz=db_m_sqmhz, port=port)


    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        self._unary_op(Network.plot_stab, None, frequency_hz=frequency_hz, port=port, n_points=n_points, label=label, style=style)


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
