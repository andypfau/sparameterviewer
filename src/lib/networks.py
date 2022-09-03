from multiprocessing.sharedctypes import Value
from .structs import LoadedSParamFile
from .bodefano import BodeFano
from .stabcircle import StabilityCircle
from .sparams import SParam, SParams


import skrf, math
import numpy as np
import logging



class Network:
    
    def __init__(self, nw: "Network|skrf.Network|LoadedSParamFile" = None):
        if isinstance(nw, Network):
            self.nw = nw.nw
        elif isinstance(nw, skrf.Network):
            self.nw = nw
        elif isinstance(nw, LoadedSParamFile):
            self.nw = nw.sparam.network
        else:
            raise ValueError()
    

    @staticmethod
    def _get_adapted_networks(a: "SParam", b: "SParam") -> "tuple(skrf.Network)":
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


    def __invert__(self) -> "Network":
        return self.invert()


    def __pow__(self, other: "Network") -> "Network":
        a_nw,b_nw = Network._get_adapted_networks(self, other)
        return Network(a_nw**b_nw)
    

    def __repr__(self):
        return f'<Network({self.nw})>'
    

    def s(self, egress_port: int = None, ingress_port: int = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False) -> SParams:
        result = []
        for ep in range(1, self.nw.number_of_ports+1):
            for ip in range(1, self.nw.number_of_ports+1):
                if egress_port is not None and ep!=egress_port:
                    continue
                if ingress_port is not None and ip!=ingress_port:
                    continue
                if rl_only and ep!=ip:
                    continue
                if il_only and ep==ip:
                    continue
                if fwd_il_only and not (ep>ip):
                    continue
                if rev_il_only and not (ep<ip):
                    continue
                result.append(SParam(self.nw.name, self.nw.f, self.nw.s[:,ep-1,ip-1], self.nw.z0[0,ep-1]))
        return result
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Network":
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
        new_nw = skrf.Network(name=self.nw.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw)
    

    def k(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.nw.name} (only valid for 2-port networks)')
        return SParam(self.nw.name, self.nw.f, self.nw.stability, self.nw.z0[0,0])
    

    def mu(self, mu: int = 1):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.mu(mu): cannot calculate stability factor of {self.nw.name} (only valid for 2-port networks)')
        if mu!=1 and mu!=2:
            raise RuntimeError(f'Network.mu(mu): mu must be 1 or 2')
        # see https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability
        if mu==1:
            p1,p2 = 0,1
        else:
            p1,p2 = 1,0
        delta = self.nw.s[:,0,0]*self.nw.s[:,1,1] - self.nw.s[:,0,1]*self.nw.s[:,1,0]
        stability_factor = (1 - np.abs(self.nw.s[:,p1,p1]**2)) / (np.abs(self.nw.s[:,p2,p2]-np.conjugate(self.nw.s[:,p1,p1])*delta) + np.abs(self.nw.s[:,1,0]*self.nw.s[:,0,1]))
        return SParam(self.nw.name, self.nw.f, stability_factor, self.nw.z0[0,0])
    

    def half(self) -> "Network":
        return Network(skrf.network.chopinhalf(self.nw))
    

    def flip(self) -> "Network":
        return Network(skrf.Network(name=self.nw.name, f=self.nw.f, s=skrf.network.flip(self.nw.s), f_unit='Hz'))
    

    def invert(self) -> "Network":
        return Network(self.nw.inv)


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
            return Network(skrf.Network(name=self.nw.name, f=self.nw.f, s=s_new, f_unit='Hz'))

        elif self.nw.number_of_ports==2:
            other_nw = skrf.Network(name=self.nw.name, f=self.nw.f, s=s_matrix, f_unit='Hz')
            if port==1:
                new_nw = other_nw ** self.nw
            elif port==2:
                new_nw = self.nw ** other_nw
            else:
                raise ValueError()
            return Network(new_nw)
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
    

    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss: float = 0, port: int = 1) -> "Network":
        z0_self = self.nw.z0[0,0]
        z0 = z0 if z0 is not None else z0_self

        # see https://cds.cern.ch/record/1415639/files/p67.pdf
        s_matrix = np.zeros([len(self.nw.f),2,2], dtype=complex)
        arg = 1j*degrees*math.pi/180 * self.nw.f/frequency_hz + loss
        sh = np.sinh(arg)
        ch = np.cosh(arg)
        zzpzz = z0*z0 + z0_self*z0_self
        zzmzz = z0*z0 - z0_self*z0_self
        ds = 2*z0*z0_self*ch + zzpzz*sh
        s_matrix[:,0,0] = s_matrix[:,1,1] = (zzmzz*sh)/ds
        s_matrix[:,1,0] = s_matrix[:,0,1] = (2*z0*z0_self)/ds
        
        return self._get_added_2port(s_matrix, port)

    
    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        stab = StabilityCircle(self.nw, frequency_hz, port)
        data = stab.get_plot_data(n_points)
        freq = np.full([n_points], frequency_hz)
        label = label if label is not None else self.nw.name
        label += f' (s.i.)' if stab.stable_inside else f' (s.o.)'
        SParam.plot_fn(freq, data, label, style)



class Networks:
    

    available_networks: "list[skrf.Network]"


    def __init__(self, nws: "list[skrf.Network]|list[Network]" = None):
        self.nws = [Network(nw) for nw in nws]


    def _broadcast(self, n: "Networks") -> "list[Network]":
        if len(n.nws) == 1:
            return [n.nws] * len(self.nws)
        elif len(n.nws) == len(self.nws):
            return self.nws
        raise ValueError(f'Argument has dimension {len(n.nws)}, but must nave 1 or {len(self.nw)}')
    

    def _unary_op(self, fn, return_type, **kwargs):
        result = []
        for nw in self.nws:
            try:
                result = fn(nw, **kwargs)
                if hasattr(result, '__len__'):
                    result.extend(result)
                else:
                    result.append(result)
            except Exception as ex:
                logging.warning(f'Unary operation <{fn}> on network <{nw.nw.name}> failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_type, **kwargs):
        result = []
        for nw,other in zip(self.nws, self._broadcast(others)):
            try:
                result = fn(nw, other, **kwargs)
                if hasattr(result, '__len__'):
                    result.extend(result)
                else:
                    result.append(result)
            except Exception as ex:
                logging.warning(f'Binary operation <{fn}> on network <{nw.name}> failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def __invert__(self) -> "Networks":
        return self._unary_op(Network.__invert__, Networks)


    def __pow__(self, other: "Networks") -> "Networks":
        return self._binary_op(Network.__pow__, other, Networks)
    

    def __repr__(self):
        if len(self.nws) == 1:
            return f'<Networks({self.nws[0]})>'
        return f'<Networks({len(self.nws)}x Network, 1st is {self.nws[0]})>'
    

    def s(self, egress_port: int, ingress_port: int) -> SParams:
        return self._unary_op(Network.s, SParams, egress_port=egress_port, ingress_port=ingress_port)
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks":
        return self._unary_op(Network.crop_f, Networks, f_start=f_start, f_end=f_end)
    

    def k(self):
        return self._unary_op(Network.k, Networks)
        
    
    def mu(self, mu: int = 1):
        return self._unary_op(Network.mu, Networks, mu=mu)
    

    def half(self) -> "Networks":
        return self._unary_op(Network.half, Networks)

    
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
        
    
    def add_tl(self, degrees: float, frequency_hz: float = 1e9, z0: float = None, loss: float = 0, port: int = 1) -> "Networks":
        return self._unary_op(Network.add_tl, Networks, degrees=degrees, frequency_hz=frequency_hz, z0=z0, loss=loss, port=port)
        

    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        self._unary_op(Network.plot_stab, None, frequency_hz=frequency_hz, port=port, n_points=n_points, label=label, style=style)
    
    
    def _count(self) -> int:
        return len(self.nws)
