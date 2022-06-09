from .structs import LoadedSParamFile
from .bodefano import BodeFano
from .stabcircle import StabilityCircle

import skrf, math, cmath, copy
import numpy as np


################################################################################
# Helper methods


################################################################################
# S-Parameter Classes


class SParam:

    plot_fn: "callable[[np.ndarray,np.ndarray,str,str], None]"

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
        freq_new = skrf.Frequency.fromf(f_new, unit='Hz')
        a_nw = skrf.Network(f=a.f, s=a.s, f_unit='Hz').interpolate(freq_new)
        b_nw = skrf.Network(f=b.f, s=b.s, f_unit='Hz').interpolate(freq_new)
        return a_nw,b_nw
    
    @staticmethod
    def _op(a: "SParam", b: "SParam", op: "callable") -> "SParam":
        if isinstance(a,int) or isinstance(a,float):
            return SParam(b.name, b.f, op(a,np.array(np.ndarray.flatten(b.s))))
        if isinstance(b,int) or isinstance(b,float):
            return SParam(a.name, a.f, op(np.array(np.ndarray.flatten(a.s)),b))
        a_nw, b_nw = SParam._adapt_f(a, b)
        a_s = np.array(np.ndarray.flatten(a_nw.s))
        b_s = np.array(np.ndarray.flatten(b_nw.s))
        c_s = op(a_s, b_s)
        return SParam(a.name, a_nw.f, c_s, a_nw.z0[0])
        
    def __truediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a/b)

    def __rtruediv__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a/b)
        
    def __mul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a*b)

    def __rmul__(self, other: "SParam|float") -> "SParam":
        return SParam._op(other, self, lambda a,b: a*b)
        
    def __add__(self, other: "SParam|float") -> "SParam":
        return SParam._op(self, other, lambda a,b: a-b)

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
    
    def plot(self, label: "str|None" = None, style: "str|None" = None):
        SParam.plot_fn(self.f, self.s, label if label is not None else self.name, style)
    
    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "SParam":
        f_start = -1e99 if f_start is None else f_start
        f_end   = +1e99 if f_end   is None else f_end
        new = [(f,s) for (f,s) in zip(self.f, self.s) if f_start<=f<=f_end]
        if len(new)<1:
            raise Exception('SParam.crop_f(): frequency out of range')
        new_f, new_s = zip(*new)
        return SParam(self.name, new_f, new_s, self.z0)
        return self._new_from_z(1/(1/self._get_z() + 1/z))
    
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
    
    def __repr__(self):
        return f'<SParam("{self.name}", f={self.f}, s={self.s})>'

    
class Network:
    
    available_networks: "list[Network]"

    @staticmethod
    def _match_name_idx(s: str, names: "list[str]"):
        result = None
        for i,n in enumerate(names):
            if s.lower() in n.lower():
                if result is not None:
                    raise RuntimeError(f'Cannot uniquely match name "{s}"')
                result = i
        if result is None:
            raise RuntimeError(f'Cannot match name "{s}"')
        return result

    def __init__(self, search_str: str, *, name: str = None, nw: "skrf.Network" = None):
        if name is not None and nw is not None:
            self.nw = nw
            self.name = name
        else:
            template = Network.available_networks[Network._match_name_idx(search_str, [n.name for n in Network.available_networks])]
            self.nw = template.nw
            self.name = template.name
    
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
        return Network(None, name=self.name, nw=a_nw**b_nw)
    
    def __repr__(self):
        return f'<Network("{self.name}", nw={self.nw})>'
    
    def s(self, egress_port: int, ingress_port: int):
        return SParam(self.name, self.nw.f, self.nw.s[:,egress_port-1,ingress_port-1], self.nw.z0[0,egress_port-1])
    
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
        new_nw = skrf.Network(f=new_f, s=new_s, f_unit='Hz')
        return Network(None, name=self.name, nw=new_nw)
    
    def k(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.name} (only valid for 2-port networks)')
        return SParam(self.name, self.nw.f, self.nw.stability, self.nw.z0[0,0])
    
    def mu(self, mu: int = 1):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.mu(mu): cannot calculate stability factor of {self.name} (only valid for 2-port networks)')
        if mu!=1 and mu!=2:
            raise RuntimeError(f'Network.mu(mu): mu must be 1 or 2')
        # see https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability
        if mu==1:
            p1,p2 = 0,1
        else:
            p1,p2 = 1,0
        delta = self.nw.s[:,0,0]*self.nw.s[:,1,1] - self.nw.s[:,0,1]*self.nw.s[:,1,0]
        stability_factor = (1 - np.abs(self.nw.s[:,p1,p1]**2)) / (np.abs(self.nw.s[:,p2,p2]-np.conjugate(self.nw.s[:,p1,p1])*delta) + np.abs(self.nw.s[:,1,0]*self.nw.s[:,0,1]))
        return SParam(self.name, self.nw.f, stability_factor, self.nw.z0[0,0])
    
    def half(self) -> "Network":
        return Network(None, name=self.name, nw=skrf.network.chopinhalf(self.nw))
    
    def flip(self) -> "Network":
        return Network(None, name=self.name, nw=skrf.Network(f=self.nw.f, s=skrf.network.flip(self.nw.s), f_unit='Hz'))
    
    def invert(self) -> "Network":
        return Network(None, name=self.name, nw=self.nw.inv)

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
            return Network(None, name=self.name, nw=skrf.Network(f=self.nw.f, s=s_new, f_unit='Hz'))

        elif self.nw.number_of_ports==2:
            other_nw = skrf.Network(f=self.nw.f, s=s_matrix, f_unit='Hz')
            if port==1:
                new_nw = other_nw ** self.nw
            elif port==2:
                new_nw = self.nw ** other_nw
            else:
                raise ValueError()
            return Network(None, name=self.name, nw=new_nw)
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
    
    def plot_stab(self, frequency_hz: float, at_output: bool = False, n_points=101, label: "str|None" = None, style: "str|None" = None):
        stab = StabilityCircle(self.nw, frequency_hz, at_output)
        fake_f = np.linspace(0, 1, n_points)
        plot = stab.get_plot_data(n_points)
        label = label if label is not None else self.name
        label += f' (s.i.)' if stab.stable_inside else f' (s.o.)'
        SParam.plot_fn(fake_f, plot, label, style)

    
################################################################################
# Parser


class ExpressionParser:

    @staticmethod
    def eval(code: str, available_networks: "list[LoadedSParamFile]", plot_fn: "callable[np.ndarray,np.ndarray,str,str]"):
            
        SParam.plot_fn = plot_fn
        Network.available_networks = [Network(None, name=nw.filename, nw=nw.sparam.network) for nw in available_networks]

        def nw(name: str) -> Network:
            return Network(name)
        
        def _get_nw(obj: "str|Network") -> Network:
            return obj if isinstance(obj, Network) else Network(obj)
        
        def s(network: "str|Network", egress_port: int, ingress_port: int) -> SParam:
            return _get_nw(network).s(egress_port, ingress_port)
        
        def k(network: "str|Network") -> SParam:
            return _get_nw(network).k()
        
        def mu(network: "str|Network", mu: int = 1) -> SParam:
            return _get_nw(network).mu(mu)
        
        def cascade(*networks: "tuple[str|Network, ...]") -> Network:
            networks = [_get_nw(n) for n in networks]
            result = networks[0]
            for i in range(1,len(networks)):
                result = result ** networks[i-1]
            return result
        
        def half(network: "Network") -> Network:
            return _get_nw(network).half()
        
        def flip(network: "Network") -> Network:
            return _get_nw(network).flip()
        
        def invert(network: "Network") -> Network:
            return ~_get_nw(network)
        
        def abs(sparam: "SParam") -> SParam:
            return sparam.abs()
        
        def db(sparam: "SParam") -> SParam:
            return sparam.db()
        
        def plot(sparam: SParam, label: "str|None" = None, style: "str|None" = None):
            sparam.plot(label, style)

        def rl_avg(sparam: SParam, f_start: "float|None" = None, f_end: "float|None" = None) -> SParam:
            return sparam.rl_avg(f_start, f_end)

        def rl_opt(sparam: SParam, f_integrate_start: "float|None" = None, f_integrate_end: "float|None" = None, f_target_start: "float|None" = None, f_target_end: "float|None" = None) -> SParam:
            return sparam.rl_opt(f_integrate_start, f_integrate_end, f_target_start, f_target_end)
        
        def crop_f(obj: "Network|SParam", f_start: "float|None" = None, f_end: "float|None" = None) -> "Network|SParam":
            return obj.crop_f(f_start, f_end)
        
        def add_sr(network: "Network", resistance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_sr(resistance, port)
        
        def add_sl(network: "Network", resistance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_sl(resistance, port)
        
        def add_sc(network: "Network", inductance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_sc(inductance, port)
        
        def add_pr(network: "Network", resistance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_pr(resistance, port)
        
        def add_pl(network: "Network", capacitance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_pl(capacitance, port)
        
        def add_pc(network: "Network", inductance: float, port: int = 1) -> "Network":
            return _get_nw(network).add_pc(inductance, port)
    
        def add_tl(network: "Network", degrees: float, frequency_hz: float = 1e9, z0: float = None, loss: float = 0, port: int = 1) -> "Network":
            return _get_nw(network).add_tl(degrees, frequency_hz, z0, loss, port)

        def plot_stab(network: "Network", frequency_hz: float, at_output: bool = False, n_points=101, label: "str|None" = None, style: "str|None" = None):
            network.plot_stab(frequency_hz, at_output, n_points, label, style)

        vars_global = {}
        vars_local = {
            'Network': Network,
            'SParam': SParam,
            'nw': nw,
            's': s,
            'k': k,
            'mu': mu,
            'half': half,
            'flip': flip,
            'invert': invert,
            'cascade': cascade,
            'add_sr': add_sr,
            'add_sl': add_sl,
            'add_sc': add_sc,
            'add_pr': add_pr,
            'add_pl': add_pl,
            'add_pc': add_pc,
            'add_tl': add_tl,
            'plot': plot,
            'plot_stab': plot_stab,
            'crop_f': crop_f,
            'abs': abs,
            'db': db,
            'rl_avg': rl_avg,
            'rl_opt': rl_opt,
            'math': math,
            'np': np,
        }
        
        for code_line in code.split('\n'):
            code_linestripped = code_line.strip()
            if code_linestripped.startswith('#'):
                continue
            if len(code_linestripped) < 1:
                continue
            _ = eval(code_linestripped, vars_global, vars_local)


    @staticmethod
    def help() -> str:
            return '''Basics
======

The basic idea is to load a network (nw), get a specific S-parameter (s), and plot it (plot):

    nw("Amplifier.s2p").s(2,1).plot("IL")

The expression use Python syntax. Everything is object-oriented,
but there are function-wrappers for convenience.

You also have access to `math` and `np` (numpy).


Objects
=======

Network
-------

    Constructor

        Network(<name_or_partial_name>)
            Returns the network that matches the provided name; e.g. Network("Amplifier") would match
            a file named "Amplifier.s2p" or "MyAmplifier01.s2p", but only if "Amplifier" is unique
            among all available networks.

    Methods

        s(<egress_port>,<ingress_port>) -> SParam
            Gets an S-parameters.

        invert() -> Network
            Inverts the ports (e.g. for de-embedding).

        flip() -> Network
            Flips the ports (e.g. to use it in reverse direction).

        half() -> Network
            Chops the network in half (e.g. for 2xTHRU de-embedding).

        k() -> SParam
            Returns the K (Rollet) stability factor (should be >1, or >0 dB).

        mu(<mu=1>) -> SParam
            Returns the µ or µ' (Edwards-Sinsky) stability factor (should be >1, or >0 dB;
            mu must be 1 or 2, default is 1).

        crop_f([f_start], [f_end]) -> Network
            Returns the same network, but with a reduced frequency range
        
        add_sr(resistance[, <port=1>]) -> Network
            Returns a network with a series resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sl(inductance[, <port=1>]) -> Network
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sc(capacitance[, <port=1>]) -> Network
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pr(resistance[, <port=1>]) -> Network
            Returns a network with a parallel resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pl(inductance[, <port=1>]) -> Network
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pc(capacitance[, <port=1>]) -> Network
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_tl(degrees, frequency_hz=1e9[, <z0=default>][, <loss=0>][, <port=1>]) -> Network
            Returns a network with a transmission line attached to the specified port.
            Works only for 1-ports and 2-ports. The length is specified in degrees at the given frequency.
            The loss is the real part of the propagation constant.
            If Z0 is not provided, the reference impedance of the corresponding port is used.
        
        rl_avg(f_start_hz=-inf, f_stop_hz=+inf) -> SParam
            Calculates the average return loss over the given frequency range.
        
        rl_opt(f_integrate_start_hz=-inf, f_integrate_stop_hz=+inf, f_target_start_hz=-inf, f_target_stop_hz=+inf) -> SParam
            Integrates the return loss over the given integration frequency range, then uses
            the Bode-Fano limit to calculate the maximum achievable return loss over the
            given target frequency range.
        
        plot_stab(frequency_hz, [<at_output=False>], [<n_points=101>], ([<label=None>],[<style="-">]):
            Plots the stability circle at the given frequency. Set at_output=True if you want to calculate the stability at
            the output, otherwise the input is calculated. It adds "s.i." (stable inside circle) or "s.o." (stable outside
            of the circle) to the plot name.

    Unary Operators

        ~
            Same as invert().

    Binary Operators

        **
            Cascades two networks.

SParam
------

    Methods

        plot([<label=None>],[<style="-">]) -> Network
            Plots the data. <label> is any string.
            <style> is a matplotlib-compatible format (e.g. "-", ":", "--", "o-").

        db() -> Network
            Converts all values to dB.

        abs() -> SParam
            Takes abs() of each value.

        crop_f([f_start=-inf], [f_end=+inf]) -> SParam.
            Returns the same S-Param, but with a reduced frequency range.

    Unary Operators

        ~
            Takes the inverse (i.e. 1/x) of each value.

    Binary Operators

        + - * /
            Applies the corresponding mathematical operator.
            Each operand can also be a numeric constant.


Functions
=========

All available functions are just shortcuts to object methods; the arguments denoted by "..." are the same as for the object methods.

    Object Method                              | Corresponding Function
    -------------------------------------------+----------------------------
    nw(<name_or_partial_name>)                 | Network(...)
    s(<network>,<egress_port>,<ingress_port>)  | Network.s(...)
    invert(<network>)                          | Network.invert()
    flip(<network>)                            | Network.flip()
    half(<network>)                            | Network.half()
    k(<network>)                               | Network.k()
    mu(<network>,...)                          | Network.mu(...)
    add_sr(<network>,...)                      | Network.add_sr(...))
    add_sl(<network>,...)                      | Network.add_sr(...)]
    add_sc(<network>,...)                      | Network.add_sr(...))
    add_pr(<network>,...)                      | Network.add_pr(...))
    add_pl(<network>,...)                      | Network.add_pl(...)]
    add_pc(<network>,...)                      | Network.add_pc(...))
    add_tl(<network>,...)                      | Network.add_tl(,...)
    plot_stab(<network>,...)                   | Network.plot_stab(,...)
    cascade(<network>,<network>[,...])         | Network**Network...
    crop_f(<network|SParam>,...)               | Network|SParam.crop_f(...)
    plot(<sparam>,...)                         | SParam.plot(...)
    db(<sparam>)                               | SParam.db()
    abs(<sparam>)                              | SParam.abs()
    rl_avg(<sparam>, ...)                      | SParam.rl_avg(...)
    rl_opt(<sparam>, ...)                      | SParam.rl_opt(...)


Examples
========

Basic
-----

    nw("Amplifier.s2p").s(2,1).plot("IL")
    nw("Amplifier.s2p").s(1,1).plot("RL",":")

Objects vs. Functions
---------------------

The following examples are all identical:

    nw("Amplifier.s2p").s(1,1).plot("RL",":")
    Network("Amplifier.s2p").s(1,1).plot("RL",":")
    plot(s(nw("Amplifier.s2p"),1,1),"RL",":")

Advanced
--------

    # calculate directivity (S42/S32) of a directional coupler
    # note that this example requires plotting in linear units, as the values are already converted to dB
    (nw("Coupler.s2p").s(4,2).db() / nw("Coupler.s2p").s(3,2).db()).plot("Directivity")

    # de-embed a 2xTHRU
    (nw("2xThru").half().invert() ** nw("DUT") ** nw("2xThru").half().invert().flip()).s(2,1).plot("De-embedded")

    # crop frequency range; this can be handy e.g. if you want to see the Smith-chart only for a specific frequency range
    nw("Amplifier.s2p").crop_f(1e9,10e9).s(1,1).plot("RL",":")

    # calculate stability factor
    nw("Amplifier").mu().plot("µ Stability Factor",":")

    # add elements to a network (in this case, a parallel cap, followed by a short transmission line)
    nw("Amplifier").s(1,1).plot("Baseline",":")
    nw("Amplifier").add_pc(400e-15).add_tl(7,2e9,25).s(1,1).plot("Optimized","-")
'''
