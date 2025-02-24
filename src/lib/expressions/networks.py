from ..structs import SParamFile
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..sparam_helpers import get_sparam_name, get_quick_params
from .sparams import SParam, SParams
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



class Network:

    
    def __init__(self, nw: "Network|skrf.Network|SParamFile" = None, name: str = None):
        self.nw: skrf.Network
        if isinstance(nw, SParamFile):
            self.nw = nw.nw
        elif isinstance(nw, Network):
            self.nw = nw.nw
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
    def _get_adapted_networks(a: "Network", b: "Network") -> "tuple(skrf.Network)":
        if len(a.nw.f)==len(b.nw.f):
            if all(af==bf for af,bf in zip(a.nw.f, b.nw.f)):
                return a.nw,b.nw
        f_min = max(min(a.nw.f), min(b.nw.f))
        f_max = min(max(a.nw.f), max(b.nw.f))
        f_new = np.array([f for f in a.nw.f if f_min<=f<=f_max])
        freq_new = skrf.Frequency.from_f(f_new, unit='Hz')
        if freq_new.npoints < 1:
            raise RuntimeError(f'The networks "{a.name}" and "{b.name}" have no overlapping frequency range')
        a_nw = a.nw.interpolate(freq_new)
        b_nw = b.nw.interpolate(freq_new)
        return a_nw,b_nw


    def __invert__(self) -> "Network":
        return self.invert()


    def __pow__(self, other: "Network") -> "Network":
        a_nw,b_nw = Network._get_adapted_networks(self, other)
        return Network(a_nw**b_nw, a_nw.name+'+'+b_nw.name)
    

    def __repr__(self):
        return f'<Network({self.nw})>'


    def s(self, egress_port: "int|str|NoneType" = None, ingress_port: "int|NoneType" = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> list[SParam]:
        
        mixed_name = None
        if isinstance(egress_port, str):
            try:
                m = re.match(r'^([cd])([cd])(\d+),(\d+)$', egress_port.lower())
                if m is None:
                    m = re.match(r'^([cd])([cd])(\d)(\d)$', egress_port.lower())
                if m is None:
                    raise ValueError()
                egress_mode, ingress_mode, egress_diffport, ingress_diffport = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
                def get_port(mode, diffport):
                    assert mode in ('c','d')
                    port = diffport
                    if mode == 'c':
                        port += self.nw.nports // 2
                    return port
                egress_port, ingress_port = get_port(egress_mode,egress_diffport), get_port(ingress_mode,ingress_diffport)
                mixed_name = get_sparam_name(egress_diffport, ingress_diffport, prefix=f'S{egress_mode}{ingress_mode}'.upper())
            except:
                raise ValueError(f'Expected a port number like <1> or <dd21>')

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
                
                if name is not None:
                    label = name
                else:
                    if mixed_name is not None:
                        label = mixed_name
                    else:
                        label = get_sparam_name(ep,ip)
                result.append(SParam(f'{self.nw.name} {label}', self.nw.f, self.nw.s[:,ep-1,ip-1], self.nw.z0[0,ep-1]))
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
        assert 0<=idx0<len(self.nw.f) and 0<=idx1<len(self.nw.f)
        if idx0<0 or idx1>=len(self.nw.f):
            raise Exception('Network.crop_f(): frequency out of range')
        new_f = self.nw.f[idx0:idx1+1]
        new_s = self.nw.s[idx0:idx1+1,:,:]
        new_nw = skrf.Network(name=self.nw.name, f=new_f, s=new_s, f_unit='Hz')
        return Network(new_nw)
    

    def k(self):
        if self.nw.number_of_ports != 2:
            raise RuntimeError(f'Network.k(): cannot calculate stability factor of {self.nw.name} (only valid for 2-port networks)')
        return SParam(f'{self.nw.name} k', self.nw.f, self.nw.stability, self.nw.z0[0,0])
    

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
        return SParam(f'{self.nw.name} µ{mu}', self.nw.f, stability_factor, self.nw.z0[0,0])
    

    def losslessness(self, egress_port_or_kind: "int|str" = None, ingress_port: int = None):
        s = self.nw.s
        s_t = np.transpose(s, (0,2,1))
        s_c = np.conjugate(s)
        prod = np.matmul(s_t, s_c)
        if (egress_port_or_kind == 'ii') and ingress_port is None:
            name = 'Losslessness_ii,worst'
            diag = np.diagonal(prod,0,1,2)
            worst_idx = np.argmax(np.abs(diag-1), (1)) # find the indices where the diagonal is the farthest away from 1
            matrix = np.take_along_axis(diag, np.expand_dims(worst_idx, 1), 1)
        elif (egress_port_or_kind == 'ij') and ingress_port is None:
            if self.nw.nports < 2:
                return []
            name = 'Losslessness_ij,worst'
            antidiag = np.copy(prod)
            for i in range(antidiag.shape[1]):
                antidiag[:,i,i] = 0
            antidiag = np.reshape(antidiag, (antidiag.shape[0],antidiag.shape[1]**2))
            worst_idx = np.argmax(np.abs(antidiag), (1)) # find the indices where the diagonal has greatest magnitude
            matrix = np.take_along_axis(antidiag, np.expand_dims(worst_idx,1), 1)
        elif egress_port_or_kind is not None and ingress_port is not None:
            name = get_sparam_name(egress_port_or_kind,ingress_port,"Losslessness")
            matrix = prod[:,egress_port_or_kind-1,ingress_port-1]
        else:
            raise ValueError(f'Network.losslessness(egress_port_or_kind,ingress_port): invalid arguments')
        return SParam(f'{self.nw.name} {name}', self.nw.f, matrix, self.nw.z0[0,0])
    

    def passivity(self):
        s = self.nw.s
        s_tc = np.conjugate(np.transpose(s, (0,2,1)))
        prod = np.matmul(s_tc, s)
        eigenvals = []
        for idx in range(prod.shape[0]):
            submat = prod[idx,:,:]
            ev = np.linalg.eigvals(submat)
            evmax = np.max(np.real(ev))
            eigenvals.append(evmax)
        return SParam(f'{self.nw.name} Passivity', self.nw.f, np.array(eigenvals), self.nw.z0[0,0])
    

    def reciprocity(self, egress_port: int = None, ingress_port: int = None):
        if self.nw.nports < 2:
            raise RuntimeError(f'Network.reciprocity(): cannot calculate reciprocity of {self.nw.name} (only valid for 2-port or higher networks)')
        s = self.nw.s
        if egress_port is None and ingress_port is None:
            name = 'Reciprocity_worst'
            errors = []
            for i in range(s.shape[1]):
                for j in range(i+1,s.shape[2]):
                    errors.append(s[:,i,j]-s[:,j,i])
            errmat = np.stack(errors)
            worst_idx = np.argmax(np.abs(errmat),(0))
            error = np.take_along_axis(errmat, np.expand_dims(worst_idx, 0), 0).reshape((s.shape[0],1))
        elif egress_port is not None and ingress_port is not None:
            if egress_port == ingress_port:
                raise ValueError(f'Network.reciprocity(egress_port,ingress_port): ports must be different')
            name = get_sparam_name(egress_port,ingress_port,"Reciprocity")
            error = s[:,egress_port-1,ingress_port-1] - s[:,ingress_port-1,egress_port-1]
        else:
            raise ValueError(f'Network.reciprocity(egress_port,ingress_port): invalid arguments')
        return SParam(f'{self.nw.name} {name}', self.nw.f, error, self.nw.z0[0,0])
    

    def half(self, method: str = 'IEEE370NZC', side: int = 1) -> "Network":
        if method=='IEEE370NZC':
            from skrf.calibration import IEEEP370_SE_NZC_2xThru # don't import on top of file, as some older versions of the package don't provide this yet
            deembed = IEEEP370_SE_NZC_2xThru(dummy_2xthru=self.nw)
            if side==1:
                return Network(deembed.s_side1, name=self.name+'_side1')
            elif side==2:
                return Network(deembed.s_side2.flipped(), name=self.name+'_side2')
            else:
                raise ValueError(f'half(): Invalid side, must be 1 or 2')
        elif method=='ChopInHalf':
            return Network(skrf.network.chopinhalf(self.nw))
        else:
            raise ValueError(f'half(): Invalid method, must be <IEEE370NZC> or <ChopInHalf>')
    

    def flip(self) -> "Network":
        return Network(skrf.Network(name=self.nw.name, f=self.nw.f, s=skrf.network.flip(self.nw.s), f_unit='Hz'), name='~'+self.name)
    

    def invert(self) -> "Network":
        return Network(self.nw.inv, name='!'+self.name)


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

    
    def plot_stab(self, frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
        stab = StabilityCircle(self.nw, frequency_hz, port)
        data = stab.get_plot_data(n_points)
        freq = np.full([n_points], frequency_hz)
        label = label if label is not None else self.nw.name
        label += f' (s.i.)' if stab.stable_inside else f' (s.o.)'
        SParam.plot_fn(freq, data, label, style)
        
    
    def quick(self, *items):
        for (e,i) in get_quick_params(*items):
            SParams(self.s(e,i)).plot()
    

    def s2m(self, ports: list = None) -> "Network":
        """
        Argument <ports>: list of ports of the single-ended input network, e.g.
            ["p1","p2","n1","n2"], which means:
            - port 1 is differential-1-positive
            - port 2 is differential-2-positive
            - port 3 is differential-1-negative
            - port 4 is differential-2-negative
        """
        new_nw = self.nw.copy()
        
        if ports is not None:
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
        assert new_nw.nports % 2 == 0
        return Network(new_nw)
    

    def m2s(self, ports: list = None) -> "Network":
        """
        Argument <ports>: list of ports of the differential input network, e.g.
            ["d1","c1","d2","c2"], which means:
            - port 1 is differential-1
            - port 2 is commonmode-1
            - port 3 is differential-2
            - port 4 is commonmode-2
        """

        new_nw = self.nw.copy()
        
        if ports is not None:
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
        return Network(new_nw)
    

    def s2z(self) -> "Network":
        nw = self.nw.copy()
        nw.s = nw.z
        nw.name += ' Impedance'
        return Network(nw)


    def s2y(self) -> "Network":
        nw = self.nw.copy()
        nw.s = nw.y
        nw.name += ' Admittance'
        return Network(nw)


    def renorm(self, z: "complex|list[complex]") -> "Network":
        nw = self.nw.copy()
        nw.renormalize(z)
        return Network(nw)


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


    def __init__(self, nws: "list[skrf.Network]|list[Network]" = None):
        self.nws = [Network(nw) for nw in nws]


    def _broadcast(self, n: "Networks") -> "list[Network]":
        if len(n.nws) == 1:
            return [n.nws[0]] * len(self.nws)
        elif len(n.nws) == len(self.nws):
            return self.nws
        raise ValueError(f'Argument has dimension {len(n.nws)}, but must nave 1 or {len(self.nws)}')
    

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
                logging.warning(f'Unary operation <{fn}> on network <{nw.nw.name}> failed ({ex}), ignoring')
        if return_type == Networks:
            return Networks(nws=result)
        elif return_type == SParams:
            return SParams(sps=result)
        else:
            return result


    def _binary_op(self, fn, others, return_type, *args, **kwargs):
        result = []
        for nw,other in zip(self.nws, self._broadcast(others)):
            try:
                r = fn(nw, other, *args, **kwargs)
                if hasattr(r, '__len__'):
                    result.extend(r)
                else:
                    result.append(r)
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
    

    def s(self, egress_port: int = None, ingress_port: int = None, rl_only: bool = False, il_only: bool = False, fwd_il_only: bool = False, rev_il_only: bool = False, name: str = None) -> SParams:
        return self._unary_op(Network.s, SParams, egress_port=egress_port, ingress_port=ingress_port, rl_only=rl_only, il_only=il_only, fwd_il_only=fwd_il_only, rev_il_only=rev_il_only, name=name)
    

    def crop_f(self, f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks":
        return self._unary_op(Network.crop_f, Networks, f_start=f_start, f_end=f_end)
    

    def k(self):
        return self._unary_op(Network.k, SParams)
        
    
    def mu(self, mu: int = 1):
        return self._unary_op(Network.mu, SParams, mu=mu)
        
    
    def passivity(self):
        return self._unary_op(Network.passivity, SParams)
        
    
    def losslessness(self, egress_port_or_kind: "int|str" = None, ingress_port: int = None):
        return self._unary_op(Network.losslessness, SParams, egress_port_or_kind=egress_port_or_kind, ingress_port=ingress_port)
    
    def reciprocity(self, egress_port: int = None, ingress_port: int = None):
        return self._unary_op(Network.reciprocity, SParams, egress_port=egress_port, ingress_port=ingress_port)
    

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
        
    
    def quick(self, *items):
        self._unary_op(Network.quick, None, *items)
        
    
    def m2s(self, ports: list = None) -> "Networks":
        return self._unary_op(Network.m2s, Networks, ports=ports)
        
    
    def s2m(self, ports: list = None) -> "Networks":
        return self._unary_op(Network.s2m, Networks, ports=ports)
    

    def s2z(self) -> "Networks":
        return self._unary_op(Network.s2z, Networks)
    

    def s2y(self) -> "Networks":
        return self._unary_op(Network.s2y, Networks)
    

    def renorm(self, z: "complex|list[complex]") -> "Networks":
        return self._unary_op(Network.renorm, Networks, z=z)


    def save(self, filename: str):
        WILDCARD = '$$'
        
        if len(self.nws) > 1:
            if WILDCARD not in filename:
                raise RuntimeError(f'Please add a wildcard ("{WILDCARD}") to the filename if you want to save multiple files.')
        
        for nw in self.nws:
            [directory, name] = os.path.split(filename)
            [name, ext] = os.path.splitext(name)
            name = sanitize_filename(name.replace(WILDCARD, nw.name))
            path = os.path.join(directory, name+ext)
            nw.save(path)


    def _count(self) -> int:
        return len(self.nws)
