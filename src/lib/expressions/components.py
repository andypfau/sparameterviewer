from __future__ import annotations
import math
import skrf
import copy
import numpy as np
import scipy.constants
from typing import override
from .networks import Network, Networks
from lib.si import SiValue



class ParametricNetwork(Network):

    @staticmethod
    def _make_series_element(f: np.ndarray, z: np.ndarray, z0: float, name:str) -> skrf.Network:
        
        if f is None or z0 is None:
            raise RuntimeError('Cannot dynamically calculate component: no frequency/impedance context given')
        assert f.shape == z.shape
        
        s = np.ndarray([len(f), 2, 2], dtype=complex)
        s[:,0,0] = s[:,1,1] =    z / (z + 2*z0)
        s[:,1,0] = s[:,0,1] = 2*z0 / (z + 2*z0)
        return skrf.Network(name=name, f=f, s=s, f_unit='Hz', z0=z0)


    def interpolate(self, f_start_or_vector_or_reference: "np.ndarray|float|Network", f_stop: float = None, f_step: float = None, n: int = None, scale='lin', z0=50)-> "ParametricNetwork":
        print(f'ParametricNetwork.interpolate() called')
        f = Network._get_interpolation_frequency(f_start_or_vector_or_reference=f_start_or_vector_or_reference, f_stop=f_stop, f_step=f_step, n=n, scale=scale)
        return self._calculate(self, f=f, z0=z0)


    def _interpolate(self, f: np.ndarray) -> "ParametricNetwork":
        print(f'ParametricNetwork._interpolate() called')
        result = copy.deepcopy(self)
        result._calculate(f=f, z0=50)
        return result



class R(ParametricNetwork):
    
    def __init__(self, r: float, topo: str):
        self._series_r = r
        self._topo = topo
        super().__init__(None, name=f'{SiValue(self._series_r,"Ω")}')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        if f is None or z0 is None:
            raise RuntimeError('Cannot dynamically calculate component: no frequency/impedance context given')
        
        z = np.full_like(f, self._series_r)
        self._nw = ParametricNetwork._make_series_element(f, z, z0, name=self._name)
        
        if self._topo == 'shunt':
            self._nw.s = Network._series_to_shunt(self._nw.s)
        else:
            assert self._topo == 'series'



class L(ParametricNetwork):
    
    def __init__(self, l: float, topo: str):
        self._series_l = l
        self._topo = topo
        super().__init__(None, name=f'{SiValue(self._series_l,"H")}')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        if f is None or z0 is None:
            raise RuntimeError('Cannot dynamically calculate component: no frequency/impedance context given')
        
        z = 1j * math.tau * f * self._series_l
        self._nw = ParametricNetwork._make_series_element(f, z, z0, name=self._name)
        
        if self._topo == 'shunt':
            self._nw.s = Network._series_to_shunt(self._nw.s)
        else:
            assert self._topo == 'series'



class C(ParametricNetwork):
    
    def __init__(self, c: float, topo: str):
        self._series_c = c
        self._topo = topo
        super().__init__(None, name=f'{SiValue(self._series_c,"F")}')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        if f is None or z0 is None:
            raise RuntimeError('Cannot dynamically calculate component: no frequency/impedance context given')
        
        z = 1 / (1j * math.tau * f * self._series_c)
        self._nw = ParametricNetwork._make_series_element(f, z, z0, name=self._name)
        
        if self._topo == 'shunt':
            self._nw.s = Network._series_to_shunt(self._nw.s)
        else:
            assert self._topo == 'series'



class Line(ParametricNetwork):
    
    def __init__(self, z: float, c_m: float, l_m: float, r_m: float, g_m: float, len: float, eps_r: float, df: float, delay: float, deg: float, at_f: float, db: float, db_m_mhz: float, db_m_sqmhz: float, topo: str = 'series', stub_gamma: complex = -1):
        self._line_z = z
        self._line_c_m = c_m
        self._line_l_m = l_m
        self._line_r_m = r_m
        self._line_g_m = g_m
        self._line_len = len
        self._line_eps_r = eps_r
        self._line_df = df
        self._line_delay = delay
        self._line_deg = deg
        self._line_at_f = at_f
        self._line_db = db
        self._line_db_m_mhz = db_m_mhz
        self._line_db_m_sqmhz = db_m_sqmhz
        self._topo = topo
        self._line_stub_gamma = stub_gamma
        super().__init__(None)

    def _calc_line_params(self, f: np.ndarray, z0: float) -> tuple[float,np.ndarray,np.ndarray,str]:
        
        def calc_attn_const(len_m: float, λ: np.ndarray) -> tuple[bool,np.ndarray]:
            if self._line_df is not None:
                if self._line_db is not None or self._line_db_m_mhz is not None or self._line_db_m_sqmhz is not None:
                    raise ValueError('Line(): need attenuation in dB, or dissipation factor')
                return (True, math.pi * self._line_df / λ)
            
            if self._line_df is not None:
                raise ValueError('Line(): need attenuation in dB, or dissipation factor')
            lossy = False
            attn_const = np.zeros_like(f, dtype=complex)
            if self._line_db is not None:
                lossy = True
                attn_const += np.log(10**(self._line_db / 20))
            if self._line_db_m_mhz is not None:
                lossy = True
                attn_const += np.log(10**(self._line_db_m_mhz * len_m * (f/1e6) / 20))
            if self._line_db_m_sqmhz is not None:
                lossy = True
                attn_const += np.log(10**(self._line_db_m_sqmhz * len_m * np.sqrt(f/1e6) / 20))
            return (lossy,attn_const)
        
        if self._line_c_m is not None or self._line_l_m is not None:
            # define line via material constants C/L/R/G per meter
            if self._line_len is None or self._line_c_m is None or self._line_l_m is None:
                raise ValueError('Line(): need all of length, capacitance and inductance per unit length')
            if self._line_z is not None or self._line_eps_r is not None or self._line_delay is not None or self._line_deg is not None or self._line_at_f is not None or self._line_db is not None or self._line_db_m_mhz is not None or self._line_db_m_sqmhz is not None or self._line_df is not None:
                raise ValueError('Line(): need either material constants, or impedance and dielectric const or phase/attenuation')
            r_m = self._line_r_m if self._line_r_m is not None else 0
            g_m = self._line_g_m if self._line_g_m is not None else 0
            lossy = (r_m != 0 or g_m != 0)
            l = self._line_len
            z = np.sqrt((r_m + 1j*math.tau*f*self._line_l_m) / (g_m + 1j*math.tau*f*self._line_c_m))
            γ = np.sqrt((r_m + 1j*math.tau*f*self._line_l_m) * (g_m + 1j*math.tau*f*self._line_c_m))
            name = f'{SiValue(self._line_len,"m")} {"Lossy " if lossy else ""}Line'
        
        elif self._line_len is not None or self._line_eps_r is not None:
            # define line via length and dielectric constant
            if self._line_len is None:
                raise ValueError('Line(): need all of length, impedance and dielectric constant')
            if self._line_c_m is not None or self._line_l_m is not None or self._line_r_m is not None or self._line_g_m is not None or self._line_delay is not None or self._line_deg is not None or self._line_at_f is not None:
                raise ValueError('Line(): need either material constants, or impedance and dielectric const or phase/attenuation')
            eps_r = self._line_eps_r if self._line_eps_r is not None else 1
            λ = scipy.constants.c / (f * np.sqrt(eps_r))
            lossy, α = calc_attn_const(self._line_len, λ)
            β = math.tau / λ
            l = self._line_len
            z = self._line_z if self._line_z is not None else z0
            γ = α + 1j*β
            name = f'{SiValue(self._line_len,"m")} {"Lossy " if lossy else ""}Line'
        
        elif self._line_deg is not None or self._line_at_f is not None:
            # define line via phase shift
            if self._line_deg is None or self._line_at_f is None:
                raise ValueError('Line(): need both phase/frequency and impedance')
            if self._line_delay is not None or self._line_c_m is not None or self._line_l_m is not None or self._line_r_m is not None or self._line_g_m is not None:
                raise ValueError('Line(): need either material constants, or impedance and dielectric const or phase/attenuation')
            eps_r = self._line_eps_r if self._line_eps_r is not None else 1
            λ = scipy.constants.c / (f * np.sqrt(eps_r))
            λ_at_f = scipy.constants.c / (self._line_at_f * np.sqrt(eps_r))
            l = (self._line_deg / 360.0) * λ_at_f
            lossy, α = calc_attn_const(l, λ)
            β = math.tau / λ
            z = self._line_z if self._line_z is not None else z0
            γ = α + 1j*β
            name = f'{self._line_deg}° {"Lossy " if lossy else ""}Line'

        elif self._line_delay is not None:
            # define line via delay
            if self._line_delay is None:
                raise ValueError('Line(): need both delay and impedance')
            if self._line_deg is not None or self._line_c_m is not None or self._line_l_m is not None or self._line_r_m is not None or self._line_g_m is not None:
                raise ValueError('Line(): need either material constants, or impedance and dielectric const or phase/attenuation')
            eps_r = self._line_eps_r if self._line_eps_r is not None else 1
            λ = scipy.constants.c / (f * np.sqrt(eps_r))
            λ_0 = scipy.constants.c / np.sqrt(eps_r)
            l = self._line_delay * λ_0
            lossy, α = calc_attn_const(l, λ)
            β = math.tau / λ
            z = self._line_z if self._line_z is not None else z0
            γ = α + 1j*β
            name = f'{SiValue(self._line_delay,"s")} {"Lossy " if lossy else ""}Line'
        
        else:
            raise ValueError('Line(): not enough parameters')
        
        return l, z, γ, name

    @override
    def _calculate(self, f: np.ndarray, z0: float):
        if f is None or z0 is None:
            raise RuntimeError('Line(): Cannot dynamically calculate component: no frequency/impedance context given')
        
        l, z, γ, name = self._calc_line_params(f, z0)

        Γ = (z0 - z) / (z0 + z)
        X = np.exp(-γ*l)
        
        s = np.ndarray([len(f), 2, 2], dtype=complex)
        s[:,0,0] = s[:,1,1] = (Γ * (1 - (X**2))) / (1 - (X**2) * (Γ**2))
        s[:,1,0] = s[:,0,1] = (X * (1 - (Γ**2))) / (1 - (X**2) * (Γ**2))
        
        if self._topo == 'shunt':
            s = Network._series_to_shunt(s, self._line_stub_gamma)
        else:
            assert self._topo == 'series'
        
        self._nw = skrf.Network(name=name, f=f, s=s, f_unit='Hz')
        self._name = name



class Phase(ParametricNetwork):
    
    def __init__(self, deg: float):
        self._shift_deg = deg
        super().__init__(None, name=f'φ({deg}°)')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        s = np.zeros([len(f),2,2], dtype=complex)
        s[:,0,1] = np.exp(1j*math.tau * (self._shift_deg/360))
        s[:,1,0] = np.exp(1j*math.tau * (self._shift_deg/360))
        self._nw = skrf.Network(name=self._name, f=f, s=s, f_unit='Hz')



class Thru(ParametricNetwork):
    
    def __init__(self):
        super().__init__(None, name='Thru')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        s = np.zeros([len(f),2,2], dtype=complex)
        s[:,0,1] = 1
        s[:,1,0] = 1
        self._nw = skrf.Network(name=self._name, f=f, s=s, f_unit='Hz')



class Iso(ParametricNetwork):
    
    def __init__(self, reverse: bool):
        self._iso_reverse = reverse
        super().__init__(None, name=f'{"Rev " if reverse else ""}Iso')
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        s = np.zeros([len(f),2,2], dtype=complex)
        if self._iso_reverse:
            s[:,0,1] = 1
        else:
            s[:,1,0] = 1
        self._nw = skrf.Network(name=self._name, f=f, s=s, f_unit='Hz')



class Term(ParametricNetwork):
    
    def __init__(self, gamma: complex = None, z: complex = None):
        self._term_gamma, self._term_z = gamma, z
        super().__init__(None)
    
    @override
    def _calculate(self, f: np.ndarray, z0: float):
        
        if self._term_gamma is not None and self._term_z is None:
            gamma = self._term_gamma
        elif self._term_z is not None and self._term_gamma is None:
            gamma = (self._term_z - 50) / (self._term_z + 50)
        elif self._term_z is None and self._term_gamma is None:
            gamma = 0
        else:
            raise ValueError('Term(): need either reflection coefficient Γ or impedance Z')

        if gamma == 0:
            name = 'Load'
        elif gamma == +1:
            name = 'Open'
        elif gamma == -1:
            name = 'Short'
        elif self._term_z is not None:
            name = f'Term<Z={self._term_z}>'
        else:
            name = f'Term<Γ={self._term_gamma}>'

        s = np.zeros([len(f),2,2], dtype=complex)
        s[:,0,0] = gamma
        s[:,1,1] = gamma
        self._nw = skrf.Network(name=name, f=f, s=s, f_unit='Hz')
        self._name = name



class Components:  # just a container for parametric networks

    class RSer(Networks):
        def __init__(self, r: float):
            super().__init__([R(r, topo='series')])

    class RShunt(Networks):
        def __init__(self, r: float):
            super().__init__([R(r, topo='shunt')])


    class LSer(Networks):
        def __init__(self, l: float):
            super().__init__([L(l, topo='series')])

    class LShunt(Networks):
        def __init__(self, l: float):
            super().__init__([L(l, topo='shunt')])


    class CSer(Networks):
        def __init__(self, c: float):
            super().__init__([C(c, topo='series')])

    class CShunt(Networks):
        def __init__(self, c: float):
            super().__init__([C(c, topo='shunt')])


    class Line(Networks):
        def __init__(self, z: float = None, c_m: float = None, l_m: float = None, r_m: float = None, g_m: float = None, len: float = None, eps_r: float = None, df: float = None, delay: float = None, deg: float = None, at_f: float = None, db: float = None, db_m_mhz: float = None, db_m_sqmhz = None):
            super().__init__([Line(z, c_m, l_m, r_m, g_m, len, eps_r, df, delay, deg, at_f, db, db_m_mhz, db_m_sqmhz, topo='series')])

    class LineStub(Networks):
        def __init__(self, z: float = None, c_m: float = None, l_m: float = None, r_m: float = None, g_m: float = None, len: float = None, eps_r: float = None, df: float = None, delay: float = None, deg: float = None, at_f: float = None, db: float = None, db_m_mhz: float = None, db_m_sqmhz = None, stub_gamma: complex = -1):
            super().__init__([Line(z, c_m, l_m, r_m, g_m, len, eps_r, df, delay, deg, at_f, db, db_m_mhz, db_m_sqmhz, topo='shunt', stub_gamma=stub_gamma)])
    

    class Phase(Networks):
        def __init__(self, deg: float):
            super().__init__([Phase(deg=deg)])


    class Thru(Networks):
        def __init__(self):
            super().__init__([Thru()])

    
    class Iso(Networks):
        def __init__(self, reverse: bool = False):
            super().__init__([Iso(reverse=reverse)])


    class Term(Networks):
        def __init__(self, gamma: complex = None, z: complex = None):
            super().__init__([Term(gamma=gamma, z=z)])
