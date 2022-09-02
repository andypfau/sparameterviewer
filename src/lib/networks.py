from .structs import LoadedSParamFile
from .bodefano import BodeFano
from .stabcircle import StabilityCircle
from .sparams import SParam, SParams


import skrf, math, os
import numpy as np
import fnmatch
import logging


class Networks:
    

    available_networks: "list[skrf.Network]"


    def __init__(self, search_pattern: str, *, nws: "list[skrf.Network]" = None):
        
        if nws is not None:
            self.nws = nws
            return
        
        self.nws = [] # type: list[skrf.Network]
        for nw in Networks.available_networks:
            if fnmatch.fnmatch(nw.name, search_pattern):
                self.nws.append(nw)
    

    @staticmethod
    def _get_adapted_networks(a: "SParams", b: "SParams") -> "tuple(skrf.Network)":
        if len(a.nw.f)==len(b.nw.f):
            if all(af==bf for af,bf in zip(a.nw.f, b.nw.f)):
                return a.nw,b.nw
        f_min = max(min(a.nw.f), min(b.nw.f))
        f_max = min(max(a.nw.f), max(b.nw.f))
        f_new = np.array([f for f in a.f if f_min<=f<=f_max])
        freq_new = skrf.Frequency.fromf(f_new, unit='Hz')
        a_nw = a.nw.interpolate(freq_new)
        b_nw = a.nw.interpolate(freq_new)
        return a_nw,b_nw


    def _broadcast(self, n: "Networks") -> "Networks":
        if len(n.nws) == 1:
            return [n.nws] * len(self.nws)
        elif len(n.nws) == len(self.nws):
            return self.nws
        raise ValueError(f'Argument has dimension {len(n.nws)}, but must nave 1 or {len(self.nw)}')
    

    def _unary_op(self, fn, return_type, **kwargs):
        result = []
        for nw in self.nws:
            try:
                result.append(fn(nw, **kwargs))
            except Exception as ex:
                logging.warning(f'Unary operation <{fn}> on network <{nw.name}> failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(None, nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_type, **kwargs):
        result = []
        for nw,other in zip(self.nws, self._broadcast(others)):
            try:
                result.append(fn(nw, other, **kwargs))
            except Exception as ex:
                logging.warning(f'Binary operation <{fn}> on network <{nw.name}> failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(None, nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def __invert__(self) -> "Networks":
        return self._unary_op(lambda nw: nw.inv, True)


    def __pow__(self, other: "Networks") -> "Networks":
        def fn(a, b):
            aa,ba = Networks._get_adapted_networks(a, b)
            return aa*ba
        return self._binary_op(fn, other, True)
    

    def __repr__(self):
        if len(self.nws) == 1:
            return f'<Networks({self.nws[0]})>'
        return f'<Networks({len(self.nws)}x Network, 1st is {self.nws[0]})>'
    

    def s(self, egress_port: int, ingress_port: int) -> SParams:
        def fn(nw):
            return SParam(nw.name, nw.f, nw.s[:,egress_port-1,ingress_port-1], nw.z0[0,egress_port-1])
        return self._unary_op(fn, SParams)
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks":
        def fn(nw, f_start, f_end):
            f_start = -1e99 if f_start is None else f_start
            f_end   = +1e99 if f_end   is None else f_end
            idx0, idx1 = +1e99, -1e99
            for idx,f in enumerate(self.nw.f):
                if f>=f_start:
                    idx0 = min(idx,idx0)
                if f<=f_end:
                    idx1 = max(idx,idx1)
            if idx0<0 or idx1>=len(self.nw.f):
                raise Exception('Network.crop_f(): frequency out of range')
            new_f = self.nw.f[idx0:idx1+1]
            new_s = self.nw.s[idx0:idx1+1,:,:]
            new_nw = skrf.Network(name=nw.name, f=new_f, s=new_s, f_unit='Hz')
            return new_nw
        return self._unary_op(fn, True, f_start=f_start, f_end=f_end)
    

    def k(self):
        def fn(nw):
            if nw.number_of_ports != 2:
                raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.name} (only valid for 2-port networks)')
            return SParams(nw.name, nw.f, nw.stability, nw.z0[0,0])
        return self._unary_op(fn, True)
        
    
    def mu(self, mu: int = 1):
        def fn(nw, mu):
            if nw.number_of_ports != 2:
                raise RuntimeError(f'Network.mu(mu): cannot calculate stability factor of {nw.name} (only valid for 2-port networks)')
            if mu!=1 and mu!=2:
                raise RuntimeError(f'Network.mu(mu): mu must be 1 or 2')
            # see https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability
            if mu==1:
                p1,p2 = 0,1
            else:
                p1,p2 = 1,0
            delta = nw.s[:,0,0]*nw.s[:,1,1] - nw.s[:,0,1]*nw.s[:,1,0]
            stability_factor = (1 - np.abs(nw.s[:,p1,p1]**2)) / (np.abs(nw.s[:,p2,p2]-np.conjugate(nw.s[:,p1,p1])*delta) + np.abs(nw.s[:,1,0]*nw.s[:,0,1]))
            return SParams(nw.name, nw.f, stability_factor, nw.z0[0,0])
        return self._unary_op(fn, True, mu=mu)
    
    def half(self) -> "Networks":
        return self._unary_op(lambda nw: skrf.network.chopinhalf(nw))
    
    def flip(self) -> "Networks":
        def fn(nw):
            return skrf.Network(name=nw.name, f=nw.f, s=skrf.network.flip(nw.s), f_unit='Hz')
        return self._unary_op(fn, True)
    
    def invert(self) -> "Networks":
        return self._unary_op(lambda nw: nw.inv, True)

    @staticmethod
    def _get_added_2port(nw: "skrf.Network", s_matrix: np.ndarray, port: int) -> "skrf.Network":
        
        if port<1 or port>nw.number_of_ports:
            raise ValueError(f'Port number {port} out of range')
        
        if nw.number_of_ports==1:
            s_new = np.zeros([len(nw.f),1,1], dtype=complex)
            s11 = s_matrix[:,0,0]
            s22 = s_matrix[:,1,1]
            s21 = s_matrix[:,1,0]
            s12 = s_matrix[:,0,1]
            s11_self = nw.s[:,0,0]
            delta = 1 - s22 * s11_self
            s_new[:,0,0] = (s11*delta + s21*s11_self*s12) / delta
            return skrf.Network(name=nw.name, f=nw.f, s=s_new, f_unit='Hz')

        elif nw.number_of_ports==2:
            other_nw = skrf.Network(f=nw.f, s=s_matrix, f_unit='Hz')
            if port==1:
                new_nw = other_nw ** nw
            elif port==2:
                new_nw = nw ** other_nw
            else:
                raise ValueError()
            skrf.Network(name=nw.name, f=nw.f, s=s_new, f_unit='Hz')

        else:
            raise RuntimeError('Impedance adding is only supported for 1-port and 2-port networks')
    
    @staticmethod
    def _get_added_z(nw: "skrf.Network", z: np.ndarray, port: int, mode: str) -> "skrf.Network":
        z0 = nw.z0[0,0]
        # see https://www.edn.com/bypass-capacitor-s-parameter-models-what-you-need-to-know/
        s_matrix = np.zeros([len(nw.f),2,2], dtype=complex)
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
        return Networks._get_added_2port(nw, s_matrix, port)
    
    def add_sr(self, resistance: float, port: int = 1) -> "Networks":
        def fn(nw, resistance, port):
            return Networks._get_added_z(nw, np.full([len(nw.f)], resistance), port, 'series')
        return self._unary_op(fn, True, resistance=resistance, port=port)
    
    def add_sl(self, inductance: float, port: int = 1) -> "Networks":
        def fn(nw, inductance, port):
            return Networks._get_added_z(1j*math.tau*nw.f*inductance, port, 'series')
        return self._unary_op(fn, True, inductance=inductance, port=port)
    
    def add_sc(self, capacitance: float, port: int = 1) -> "Networks":
        def fn(nw, capacitance, port):
            return Networks._get_added_z(1/(1j*math.tau*nw.f*capacitance), port, 'series')
        return self._unary_op(fn, True, capacitance=capacitance, port=port)
    
    def add_pr(self, resistance: float, port: int = 1) -> "Networks":
        def fn(nw, resistance, port):
            return Networks._get_added_z(np.full([len(nw.f)], resistance), port, 'parallel')
        return self._unary_op(fn, True, resistance=resistance, port=port)
    
    def add_pl(self, inductance: float, port: int = 1) -> "Networks":
        def fn(nw, inductance, port):
            return Networks._get_added_z(1j*math.tau*nw.f*inductance, port, 'parallel')
        return self._unary_op(fn, True, inductance=inductance, port=port)
    
    def add_pc(self, capacitance: float, port: int = 1) -> "Networks":
        def fn(nw, capacitance, port):
            return Networks._get_added_z(1/(1j*math.tau*nw.f*capacitance), port, 'parallel')
        return self._unary_op(fn, True, capacitance=capacitance, port=port)
    
    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss: float = 0, port: int = 1) -> "Networks":
        def fn(nw, degrees, frequency_hz, z0, loss, port):
            z0_self = self.nw.z0[0,0]
            z0 = z0 if z0 is not None else z0_self

            # see https://cds.cern.ch/record/1415639/files/p67.pdf
            s_matrix = np.zeros([len(nw.f),2,2], dtype=complex)
            arg = 1j*degrees*math.pi/180 * nw.f/frequency_hz + loss
            sh = np.sinh(arg)
            ch = np.cosh(arg)
            zzpzz = z0*z0 + z0_self*z0_self
            zzmzz = z0*z0 - z0_self*z0_self
            ds = 2*z0*z0_self*ch + zzpzz*sh
            s_matrix[:,0,0] = s_matrix[:,1,1] = (zzmzz*sh)/ds
            s_matrix[:,1,0] = s_matrix[:,0,1] = (2*z0*z0_self)/ds
            
            return Networks._get_added_2port(nw, s_matrix, port)
        
        return self._unary_op(fn, True, degrees=degrees, frequency_hz=frequency_hz, z0=z0, loss=loss, port=port)

    
    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        def fn(nw, frequency_hz, port, n_points, label, style):
            stab = StabilityCircle(nw, frequency_hz, port)
            data = stab.get_plot_data(n_points)
            freq = np.full([n_points], frequency_hz)
            label = label if label is not None else self.name
            label += f' (s.i.)' if stab.stable_inside else f' (s.o.)'
            SParams.plot_fn(freq, data, label, style)
        self._unary_op(fn, False, frequency_hz=frequency_hz, port=port, n_points=n_points, label=label, style=style)
    
    
    def _count(self) -> int:
        return len(self.nws)
